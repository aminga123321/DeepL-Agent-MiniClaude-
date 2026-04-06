"""
消息格式构建器
"""

from typing import List, Dict, Any
from agent.models import ToolCall


class MessageBuilder:
    """构建 Anthropic API 格式的消息"""
    
    @staticmethod
    def build_system_prompt(workdir: str, skills_description: str, tools_description: str = "") -> str:
        """构建系统提示"""
        tools_section = ""
        if tools_description:
            tools_section = f"\n\n## Available Tools\n\n{tools_description}"
        
        return f"""You are a coding agent at {workdir}.
You have access to tools that can execute commands, read/write files, and load specialized skills.{tools_section}

Skills available (use load_skill to get full instructions):
{skills_description}

Important: 
- If the user asks a simple question that doesn't require file access or command execution, 
  just answer directly without calling any tools.
- Only use tools when necessary (reading files, executing commands, loading skills).

Be concise and helpful."""
    
    @staticmethod
    def build_user_message(content: str) -> Dict[str, Any]:
        """构建用户消息"""
        return {
            "role": "user",
            "content": content
        }
    
    @staticmethod
    def build_assistant_message(content: str, tool_calls: List[ToolCall] = None) -> Dict[str, Any]:
        """构建助手消息"""
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
            return {
                "role": "assistant",
                "content": content_list
            }
        else:
            return {
                "role": "assistant",
                "content": content
            }
    
    @staticmethod
    def build_tool_result(tool_use_id: str, result: str) -> Dict[str, Any]:
        """构建工具结果消息"""
        return {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result
            }]
        }