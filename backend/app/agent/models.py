"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    input: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "input": self.input
        }


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    
    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_use_id: str
    content: str
    success: bool = True
    error: Optional[str] = None