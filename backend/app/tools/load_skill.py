from pathlib import Path
from typing import Dict, Any

from .base import BaseTool


class LoadSkillTool(BaseTool):
    name = "load_skill"
    description = "Load specialized skill/knowledge by name"
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Skill name"}
        },
        "required": ["name"]
    }
    
    def __init__(self, workdir: Path, skill_loader=None):
        self.workdir = workdir
        self.skill_loader = skill_loader
    
    def set_loader(self, loader):
        self.skill_loader = loader
    
    async def execute(self, args: Dict[str, Any]) -> str:
        name = args.get("name")
        if not self.skill_loader:
            return "Error: Skill loader not initialized"
        return self.skill_loader.get_content(name)