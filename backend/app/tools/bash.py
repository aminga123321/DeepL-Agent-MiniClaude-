import asyncio
import shutil
import platform
from pathlib import Path
from typing import Dict, Any

from .base import BaseTool


class BashTool(BaseTool):
    name = "bash"
    description = "Execute a shell command"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command to execute"
            }
        },
        "required": ["command"]
    }
    
    def __init__(self, workdir: Path):
        self.workdir = workdir
    
    async def execute(self, args: Dict[str, Any]) -> str:
        command = args.get("command", "").strip()
        if not command:
            return "Error: Empty command"
        
        # 检测 WSL
        if platform.system() == "Windows" and shutil.which("wsl"):
            process = await asyncio.create_subprocess_exec(
                "wsl", "bash", "-c", command,
                cwd=self.workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            process = await asyncio.create_subprocess_exec(
                "bash", "-c", command,
                cwd=self.workdir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        stdout, stderr = await process.communicate()
        output = (stdout.decode() + stderr.decode()).strip()
        return output if output else "(no output)"