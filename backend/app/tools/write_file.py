from pathlib import Path
from typing import Dict, Any

from .base import BaseTool


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to file"
    input_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"}
        },
        "required": ["path", "content"]
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
        content = args.get("content", "")
        
        try:
            safe_path = self._safe_path(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content)
            return f"Wrote {len(content)} bytes to {path}"
        except Exception as e:
            return f"Error: {str(e)}"