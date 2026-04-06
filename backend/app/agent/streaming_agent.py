"""
流式 Agent - 主控逻辑
"""

import os
import asyncio
from pathlib import Path
from typing import Callable, Awaitable, Optional

from anthropic import Anthropic
from dotenv import load_dotenv

from agent.models import LLMResponse, ToolCall
from agent.context import Context
from agent.message_builder import MessageBuilder
from agent.event_handler import EventHandler

load_dotenv(override=True)


class StreamingAgent:
    """流式 Agent - 支持动态工具"""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        workdir: Optional[Path] = None,
        max_iterations: int = 100
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.workdir = workdir or Path.cwd()
        self.max_iterations = max_iterations
        
        # 初始化组件
        self.context = Context()
        self.message_builder = MessageBuilder()
        
        # 初始化 Anthropic 客户端
        self.client = Anthropic(
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            api_key=os.getenv("ANTHROPIC_API_KEY", "dummy")
        )
        self.model = os.getenv("MODEL_ID", "claude-3-5-sonnet-20241022")
        
        # 工具系统（外部注入）
        self.tool_registry = None
        self.skill_loader = None
    
    def set_tool_registry(self, registry):
        """设置工具注册中心"""
        self.tool_registry = registry
    
    def set_skill_loader(self, loader):
        """设置技能加载器"""
        self.skill_loader = loader
    
    def _get_system_prompt(self) -> str:
        """获取系统提示"""
        skills_desc = self.skill_loader.get_descriptions() if self.skill_loader else "(no skills available)"
        
        # 获取工具描述
        tools_desc = ""
        if self.tool_registry:
            tools_list = []
            for tool in self.tool_registry.list_all():
                tools_list.append(f"- {tool.name}: {tool.description}")
            tools_desc = "\n".join(tools_list)
        
        return self.message_builder.build_system_prompt(
            workdir=str(self.workdir),
            skills_description=skills_desc,
            tools_description=tools_desc
        )
    
    def _get_tools_schemas(self) -> list:
        """获取工具 schema"""
        if self.tool_registry:
            return self.tool_registry.list_schemas()
        return []
    
    async def _call_llm(self, send_callback: Callable[[dict], Awaitable[None]]) -> LLMResponse:
        """调用 LLM，返回结构化响应"""
        handler = EventHandler(send_callback)
        
        with self.client.messages.stream(
            model=self.model,
            system=self._get_system_prompt(),
            messages=self.context.get_messages(),
            tools=self._get_tools_schemas(),
            max_tokens=4096,
            temperature=0.7
        ) as stream:
            for event in stream:
                print(f"vent: {event}")
                await handler.process_event(event)
        
        content, tool_calls = handler.get_result()
        return LLMResponse(content=content, tool_calls=tool_calls)
    
    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """执行工具"""
        if not self.tool_registry:
            return f"Error: Tool registry not initialized"
        
        try:
            return await self.tool_registry.execute(tool_name, args)
        except KeyError:
            return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def process_message(
        self,
        user_message: str,
        send_callback: Callable[[dict], Awaitable[None]]
    ) -> None:
        """处理用户消息"""
        
        # 1. 添加用户消息
        self.context.add_user_message(user_message)
        
        # 2. 开始处理
        await send_callback({"type": "start"})
        
        # 3. ReAct 循环
        for iteration in range(self.max_iterations):
            # 调用 LLM
            response = await self._call_llm(send_callback)
            
            # 判断是否有工具调用
            if not response.has_tool_calls:
                # 无工具：添加助手消息，结束
                self.context.add_assistant_message(response.content)
                await send_callback({"type": "done"})
                return
            
            # 有工具：添加助手消息（包含工具调用）
            self.context.add_assistant_message(response.content, response.tool_calls)
            
            # 执行工具
            for tool_call in response.tool_calls:
                result = await self._execute_tool(tool_call.name, tool_call.input)
                
                # 添加工具结果
                self.context.add_tool_result(tool_call.id, result)
                
                # 发送工具结果到前端
                await send_callback({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result[:500] if result else "(no output)"
                })
                await asyncio.sleep(0)
            
            # 继续循环（下一轮 LLM 会看到工具结果）
        
        # 超过最大迭代次数
        await send_callback({
            "type": "error",
            "content": f"Agent 执行超过最大迭代次数 ({self.max_iterations})"
        })