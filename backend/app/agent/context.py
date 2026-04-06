"""
消息历史管理
"""
import sys
print(sys.path)

from typing import List, Dict, Any, Optional
from agent.models import ToolCall


class Context:
    """管理对话消息历史"""
    
    def __init__(self, max_messages: int = 100):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append({
            "role": "user",
            "content": content
        })
        self._trim()
    
    def add_assistant_message(self, content: str, tool_calls: List[ToolCall] = None) -> None:
        """添加助手消息（可能包含工具调用）"""
        if tool_calls:
            content_list = []
            if content:
                content_list.append({
                    "type": "text",
                    "text": content
                })
            for tc in tool_calls:
                content_list.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.input
                })
            self.messages.append({
                "role": "assistant",
                "content": content_list
            })
        else:
            self.messages.append({
                "role": "assistant",
                "content": content
            })
        self._trim()
    
    def add_tool_result(self, tool_use_id: str, result: str) -> None:
        """添加工具执行结果"""
        self.messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result
            }]
        })
        self._trim()
    
    def _trim(self):
        """超出限制时，删除最早的消息"""
        while len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """获取所有消息"""
        return self.messages
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """获取最后一条消息"""
        return self.messages[-1] if self.messages else None
    
    def get_last_n_messages(self, n: int) -> List[Dict[str, Any]]:
        """获取最后 N 条消息"""
        return self.messages[-n:] if self.messages else []
    
    def clear(self) -> None:
        """清空消息历史"""
        self.messages = []
    
    def __len__(self) -> int:
        return len(self.messages)