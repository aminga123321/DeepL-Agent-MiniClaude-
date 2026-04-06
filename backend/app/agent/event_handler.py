"""
流式事件处理器
"""

import json
import asyncio
from typing import Callable, Awaitable, List, Dict, Any

from agent.models import ToolCall


class EventHandler:
    """处理 Anthropic 流式事件"""
    
    def __init__(self, send_callback: Callable[[dict], Awaitable[None]]):
        self.send_callback = send_callback
        self.content: str = ""
        self.tool_calls: List[ToolCall] = []
        
        # 临时变量
        self._current_tool: Dict[str, Any] = None
        self._current_tool_input: str = ""
    
    async def process_event(self, event) -> None:
        """处理单个事件"""
        
        # 消息开始
        if event.type == "message_start":
            await self._handle_message_start(event)
        
        # 内容块开始
        elif event.type == "content_block_start":
            await self._handle_content_block_start(event)
        
        # 内容块增量
        elif event.type == "content_block_delta":
            await self._handle_content_block_delta(event)
        
        # 内容块结束
        elif event.type == "content_block_stop":
            await self._handle_content_block_stop(event)
        
        # 消息增量
        elif event.type == "message_delta":
            await self._handle_message_delta(event)
        
        # 消息结束
        elif event.type == "message_stop":
            await self._handle_message_stop(event)
    
    async def _handle_message_start(self, event) -> None:
        """处理消息开始"""
        await self.send_callback({
            "type": "message_start",
            "message": {
                "id": event.message.id,
                "model": event.message.model,
                "role": event.message.role
            }
        })
        await asyncio.sleep(0)
    
    async def _handle_content_block_start(self, event) -> None:
        """处理内容块开始"""
        block_type = event.content_block.type
        
        await self.send_callback({
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
            self._current_tool = {
                "id": event.content_block.id,
                "name": event.content_block.name
            }
            self._current_tool_input = ""
    
    async def _handle_content_block_delta(self, event) -> None:
        """处理内容块增量"""
        # 文本增量
        if hasattr(event.delta, 'text'):
            text = event.delta.text
            self.content += text
            await self.send_callback({
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
            self._current_tool_input += event.delta.partial_json
    
    async def _handle_content_block_stop(self, event) -> None:
        """处理内容块结束"""
        # 如果是工具调用，解析参数
        if self._current_tool and self._current_tool_input:
            try:
                tool_input = json.loads(self._current_tool_input)
                tool_call = ToolCall(
                    id=self._current_tool["id"],
                    name=self._current_tool["name"],
                    input=tool_input
                )
                self.tool_calls.append(tool_call)
                
                await self.send_callback({
                    "type": "tool_use",
                    "id": tool_call.id,
                    "name": tool_call.name,
                    "input": tool_call.input
                })
                await asyncio.sleep(0)
            except json.JSONDecodeError as e:
                print(f"解析工具参数失败: {e}")
            
            self._current_tool = None
            self._current_tool_input = ""
        
        await self.send_callback({
            "type": "content_block_stop",
            "index": event.index
        })
        await asyncio.sleep(0)
    
    async def _handle_message_delta(self, event) -> None:
        """处理消息增量"""
        await self.send_callback({
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
    
    async def _handle_message_stop(self, event) -> None:
        """处理消息结束"""
        await self.send_callback({
            "type": "message_stop"
        })
        await asyncio.sleep(0)
    
    def get_result(self):
        """获取解析结果"""
        return self.content, self.tool_calls