from pathlib import Path
from typing import Dict, Any

from .base import BaseTool


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read file contents"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "limit": {"type": "integer", "description": "Max lines"}
        },
        "required": ["path"]
    }
    
    def __init__(self, workdir: Path):
        self.workdir = workdir
    
    def _safe_path(self, path: str) -> Path:
        full = (self.workdir / path).resolve()
        if not full.is_relative_to(self.workdir):
            raise ValueError("Path escapes workspace")
        return full
    
    async def execute(self, args: Dict[str, Any]) -> str:
        path = args.get("path")
        limit = args.get("limit")
        
        try:
            safe_path = self._safe_path(path)
            lines = safe_path.read_text().splitlines()
            if limit and limit < len(lines):
                lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
            content = "\n".join(lines)
            return content[:50000] if content else "(empty file)"
        except Exception as e:
            return f"Error: {str(e)}"