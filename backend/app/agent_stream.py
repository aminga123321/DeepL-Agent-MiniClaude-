"""

支持动态工具注册和执行
"""

import os
import json
import asyncio
import time
import sys
from pathlib import Path
from typing import Callable, Awaitable, Dict, Any, Optional

from anthropic import Anthropic
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).parent))
# 导入工具系统
from tools.__init__ import registry, register_builtin_tools
from skill_loader import SkillLoader

load_dotenv(override=True)

# 配置
WORKDIR = Path.cwd()
SKILLS_DIR = WORKDIR / "skills"

# Anthropic 客户端
client = Anthropic(
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
    api_key=os.getenv("ANTHROPIC_API_KEY", "dummy")
)
MODEL = os.getenv("MODEL_ID", "claude-3-5-sonnet-20241022")

# 技能加载器
skill_loader = SkillLoader(SKILLS_DIR)

# 系统提示
SYSTEM_PROMPT = f"""You are a coding agent at {WORKDIR}.
You have access to tools that can execute commands, read/write files, and load specialized skills.

Skills available (use load_skill to get full instructions):
{skill_loader.get_descriptions()}

When you need specialized knowledge (like PDF processing, code review), call load_skill first.
Be concise and helpful."""


class StreamingAgent:
    """流式 Agent - 支持动态工具"""
    
    def __init__(self, session_id: str, user_id: str, workdir: Optional[Path] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.workdir = workdir or WORKDIR
        self.messages = []
        
        # 初始化工具系统
        self._init_tools()
    
    def _init_tools(self):
        """初始化工具系统"""
        # 注册内置工具
        register_builtin_tools(self.workdir)
        
        # 设置 skill_loader 给 load_skill 工具
        load_skill_tool = registry.get("load_skill")
        if load_skill_tool and hasattr(load_skill_tool, 'set_loader'):
            load_skill_tool.set_loader(skill_loader)
    
    def _get_tools_schemas(self) -> list:
        """获取所有工具的 schema（给 LLM）"""
        return registry.list_schemas()
    
    async def _execute_tool(self, tool_name: str, args: dict) -> str:
        """异步执行工具"""
        try:
            return await registry.execute(tool_name, args)
        except KeyError:
            return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def process_message(self, user_message: str, send_callback: Callable[[dict], Awaitable[None]]):
        """处理用户消息，流式推送结果"""
        
        # 添加用户消息
        self.messages.append({"role": "user", "content": user_message})
        
        # ReAct 循环
        max_iterations = 100
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # 调用 Anthropic API（流式）
                with client.messages.stream(
                    model=MODEL,
                    system=SYSTEM_PROMPT,
                    messages=self.messages,
                    tools=self._get_tools_schemas(),
                    max_tokens=4096,
                    temperature=0.7
                ) as stream:
                    
                    full_content = ""
                    tool_uses = []
                    current_tool = None
                    current_tool_input = ""
                    
                    for event in stream:
                        print(f"Event: {event}")
                        
                        # ========== 消息开始 ==========
                        if event.type == "message_start":
                            await send_callback({
                                "type": "message_start",
                                "message": {
                                    "id": event.message.id,
                                    "model": event.message.model,
                                    "role": event.message.role
                                }
                            })
                            await asyncio.sleep(0)
                        
                        # ========== 内容块开始 ==========
                        elif event.type == "content_block_start":
                            block_type = event.content_block.type
                            
                            await send_callback({
                                "type": "content_block_start",
                                "index": event.index,
                                "content_block": {
                                    "type": block_type,
                                    "name": getattr(event.content_block, "name", None),
                                    "id": getattr(event.content_block, "id", None)
                                }
                            })
                            await asyncio.sleep(0)
                            
                            # 如果是工具调用，初始化
                            if block_type == "tool_use":
                                current_tool = {
                                    "id": event.content_block.id,
                                    "name": event.content_block.name,
                                    "input": {}
                                }
                                current_tool_input = ""
                        
                        # ========== 内容块增量 ==========
                        elif event.type == "content_block_delta":
                            # 文本增量
                            if hasattr(event.delta, 'text'):
                                text = event.delta.text
                                full_content += text
                                await send_callback({
                                    "type": "content_block_delta",
                                    "index": event.index,
                                    "delta": {
                                        "type": "text_delta",
                                        "text": text
                                    }
                                })
                                await asyncio.sleep(0)
                            
                            # 工具参数增量
                            elif hasattr(event.delta, 'partial_json'):
                                current_tool_input += event.delta.partial_json
                        
                        # ========== 内容块结束 ==========
                        elif event.type == "content_block_stop":
                            # 如果是工具调用，解析完整参数
                            if current_tool and current_tool_input:
                                try:
                                    current_tool["input"] = json.loads(current_tool_input)
                                    tool_uses.append(current_tool)
                                    
                                    # 发送完整的工具调用信息
                                    await send_callback({
                                        "type": "tool_use",
                                        "id": current_tool["id"],
                                        "name": current_tool["name"],
                                        "input": current_tool["input"]
                                    })
                                    await asyncio.sleep(0)
                                except json.JSONDecodeError as e:
                                    print(f"解析工具参数失败: {e}, 原始: {current_tool_input}")
                                
                                current_tool = None
                                current_tool_input = ""
                            
                            await send_callback({
                                "type": "content_block_stop",
                                "index": event.index
                            })
                            await asyncio.sleep(0)
                        
                        # ========== 消息增量 ==========
                        elif event.type == "message_delta":
                            await send_callback({
                                "type": "message_delta",
                                "delta": {
                                    "stop_reason": event.delta.stop_reason,
                                    "stop_sequence": event.delta.stop_sequence
                                },
                                "usage": {
                                    "output_tokens": event.usage.output_tokens
                                }
                            })
                            await asyncio.sleep(0)
                        
                        # ========== 消息结束 ==========
                        elif event.type == "message_stop":
                            await send_callback({
                                "type": "message_stop"
                            })
                            await asyncio.sleep(0)
                    
                    # ========== 处理工具调用 ==========
                    if tool_uses:
                        # 构建 assistant 消息（包含文本和工具调用）
                        assistant_content = []
                        
                        if full_content:
                            assistant_content.append({
                                "type": "text",
                                "text": full_content
                            })
                        
                        for tool in tool_uses:
                            assistant_content.append({
                                "type": "tool_use",
                                "id": tool["id"],
                                "name": tool["name"],
                                "input": tool["input"]
                            })
                        
                        self.messages.append({
                            "role": "assistant",
                            "content": assistant_content
                        })
                        await asyncio.sleep(0)
                        
                        # 执行工具
                        tool_results = []
                        for tool in tool_uses:
                            result = await self._execute_tool(tool["name"], tool["input"])
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool["id"],
                                "content": result
                            })
                            
                            # 发送工具结果
                            await send_callback({
                                "type": "tool_result",
                                "tool_use_id": tool["id"],
                                "content": result[:500] if result else "(no output)"
                            })
                            await asyncio.sleep(0)
                        
                        # 添加工具结果到消息历史
                        self.messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                        
                        # 继续下一轮循环
                        continue
                    
                    # ========== 没有工具调用，完成 ==========
                    if full_content:
                        self.messages.append({"role": "assistant", "content": full_content})
                    
                    return
                    
            except Exception as e:
                await send_callback({
                    "type": "error",
                    "content": f"LLM 调用失败: {str(e)}"
                })
                await asyncio.sleep(0)
                return
        
        # 超过最大迭代次数
        await send_callback({
            "type": "error",
            "content": f"Agent 执行超过最大迭代次数 ({max_iterations})"
        })