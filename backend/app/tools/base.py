from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseTool(ABC):
    """工具基类"""
    
    name: str = None
    description: str = None
    input_schema: Dict = None
    
    @abstractmethod
    async def execute(self, args: Dict[str, Any]) -> str:
        """执行工具"""
        pass
    
    def to_anthropic_schema(self) -> Dict:
        """转成 Anthropic 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }


class ToolRegistry:
    """工具注册中心"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    # 增加工具
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
    
    # 获取工具
    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
        return self._tools[name]
    
    # 获取所有工具
    def list_all(self) -> List[BaseTool]:
        return list(self._tools.values())
    
    # 获取所有工具的 schema（给 LLM）
    def list_schemas(self) -> List[Dict]:
        return [tool.to_anthropic_schema() for tool in self._tools.values()]
    
    # 执行工具
    async def execute(self, name: str, args: Dict[str, Any]) -> str:
        tool = self.get(name)
        return await tool.execute(args)