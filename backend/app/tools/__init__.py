from .base import ToolRegistry, BaseTool
from .bash import BashTool
from .read_file import ReadFileTool
from .write_file import WriteFileTool
from .load_skill import LoadSkillTool

# 全局注册中心实例
registry = ToolRegistry()

def register_builtin_tools(workdir):
    """注册所有内置工具"""
    registry.register(BashTool(workdir))
    registry.register(ReadFileTool(workdir))
    registry.register(WriteFileTool(workdir))
    registry.register(LoadSkillTool(workdir))

__all__ = [
    "BaseTool",
    "ToolRegistry", 
    "registry",
    "register_builtin_tools",
    "BashTool",
    "ReadFileTool", 
    "WriteFileTool",
    "LoadSkillTool"
]