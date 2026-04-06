import os
import re
import subprocess
import json
import asyncio
from pathlib import Path
from typing import Callable, Awaitable
import time  
from anthropic import Anthropic
from dotenv import load_dotenv
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





SKILL_LOADER = SkillLoader(SKILLS_DIR)

# 系统提示
SYSTEM_PROMPT = f"""You are a coding agent at {WORKDIR}.
You have access to tools that can execute commands, read/write files, and load specialized skills.

Skills available (use load_skill to get full instructions):
{SKILL_LOADER.get_descriptions()}

When you need specialized knowledge (like PDF processing, code review), call load_skill first.
Be concise and helpful."""


class StreamingAgent:
    """流式 Agent - 使用 Anthropic SDK"""
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.messages = []
        self.tools = self._get_tools()
    
    def _get_tools(self):
        """定义可用工具（Anthropic 格式）"""
        return [
            {
                "name": "bash",
                "description": "Run a shell command.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Shell command to execute"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "read_file",
                "description": "Read file contents.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "limit": {"type": "integer", "description": "Max lines to read"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "write_file",
                "description": "Write content to file.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"},
                        "content": {"type": "string", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "load_skill",
                "description": "Load specialized knowledge by name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Skill name to load"}
                    },
                    "required": ["name"]
                }
            }
        ]
    
    def _safe_path(self, p: str) -> Path:
        """确保路径在工作目录内"""
        path = (WORKDIR / p).resolve()
        if not path.is_relative_to(WORKDIR):
            raise ValueError(f"Path escapes workspace: {p}")
        return path
    
    def _execute_tool(self, tool_name: str, args: dict) -> str:
        """执行工具并返回结果"""
        try:
            if tool_name == "bash":
                command = args.get("command", "")
                dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
                if any(d in command for d in dangerous):
                    return "Error: Dangerous command blocked"
                result = subprocess.run(
                    ["wsl", "bash", "-c", command], cwd=WORKDIR,
                    capture_output=True, text=True, timeout=120
                )
                output = (result.stdout + result.stderr).strip()
                return output[:50000] if output else "(no output)"
            
            elif tool_name == "read_file":
                path = args.get("path")
                limit = args.get("limit")
                lines = self._safe_path(path).read_text().splitlines()
                if limit and limit < len(lines):
                    lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
                return "\n".join(lines)[:50000]
            
            elif tool_name == "write_file":
                path = args.get("path")
                content = args.get("content")
                fp = self._safe_path(path)
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content)
                return f"Wrote {len(content)} bytes to {path}"
            
            elif tool_name == "load_skill":
                name = args.get("name")
                return SKILL_LOADER.get_content(name)
            
            else:
                return f"Unknown tool: {tool_name}"
                
        except Exception as e:
            return f"Error: {e}"
    
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
                    tools=self.tools,
                    max_tokens=4096,
                    temperature=0.7
                ) as stream:
                    
                    full_content = ""
                    tool_uses = []
                    current_tool = None
                    current_tool_input = ""
                    
                    for event in stream:
                        print(f"事件: {event}")
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
                                full_content += event.delta.text
                                await send_callback({
                                    "type": "content_block_delta",
                                    "index": event.index,
                                    "delta": {
                                        "type": "text_delta",
                                        "text": event.delta.text
                                    }
                                })
                                await asyncio.sleep(0)
                                print(f"发送: {event.delta.text}, 时间: {time.time()}")  # 加这行
                            
                            # 工具参数增量
                            elif hasattr(event.delta, 'partial_json'):
                                current_tool_input += event.delta.partial_json
                                # 可选：发送参数增量（前端可以忽略）
                                # await send_callback({
                                #     "type": "content_block_delta",
                                #     "index": event.index,
                                #     "delta": {
                                #         "type": "input_json_delta",
                                #         "partial_json": event.delta.partial_json
                                #     }
                                # })
                        
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
                            result = self._execute_tool(tool["name"], tool["input"])
                            
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