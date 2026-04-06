"""
Agent 工厂 - 集成工具系统和技能加载器
"""

import sys
import os
from pathlib import Path

from agent.streaming_agent import StreamingAgent
from tools.__init__ import registry, register_builtin_tools
from skill_loader import SkillLoader


class AgentFactory:
    """Agent 工厂"""
    
    @staticmethod
    def create(session_id: str, user_id: str, workdir: Path = None):
        workdir = workdir or Path.cwd()
        
        # 注册内置工具
        register_builtin_tools(workdir)
        
        # 设置技能加载器到 load_skill 工具
        skill_loader = SkillLoader(workdir / "skills")
        load_skill_tool = registry.get("load_skill")
        if load_skill_tool and hasattr(load_skill_tool, 'set_loader'):
            load_skill_tool.set_loader(skill_loader)
        
        # 创建 Agent
        agent = StreamingAgent(session_id, user_id, workdir)
        agent.set_tool_registry(registry)
        agent.set_skill_loader(skill_loader)
        
        return agent


__all__ = ["StreamingAgent", "AgentFactory"]