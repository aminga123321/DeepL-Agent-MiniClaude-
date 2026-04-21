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

    def _convert_windows_path_to_wsl(self, windows_path: Path) -> str:
        """将 Windows 路径转换为 WSL 路径（例如 D:\foo → /mnt/d/foo）"""
        path_str = str(windows_path)
        # 处理驱动器号
        if len(path_str) >= 2 and path_str[1] == ':':
            drive = path_str[0].lower()
            rest = path_str[2:].replace('\\', '/')
            return f"/mnt/{drive}{rest}"
        return path_str.replace('\\', '/')

    def _is_wsl_available(self) -> bool:
        """检查 WSL 是否可用"""
        import platform
        import shutil
        return platform.system() == "Windows" and shutil.which("wsl.exe")

    async def execute(self, args: Dict[str, Any]) -> str:
        command = args.get("command", "").strip()
        if not command:
            return "Error: Empty command"

        use_wsl = self._is_wsl_available()
        cwd = str(self.workdir)
        env = None
        if use_wsl:
            # 设置环境变量抑制警告
            import os
            env = os.environ.copy()
            env.update({"WSL_UTF8": "1", "LANG": "C.UTF-8"})

        try:
            if use_wsl:
                # 使用 wsl.exe --cd 设置工作目录
                windows_path = str(self.workdir)
                # 构建 wsl 命令
                process = await asyncio.create_subprocess_exec(
                    "wsl.exe", "--cd", windows_path, "bash", "-c", command,
                    env=env,  # 可设置 WSL_UTF8 等环境变量
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    "bash", "-c", command,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

            # 设置超时（30秒）
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                return "Error: Command timed out after 30 seconds"

            # 解码输出，优先使用 UTF-8
            import locale
            try:
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                encoding = locale.getpreferredencoding()
                stdout_text = stdout.decode(encoding, errors='replace')
                stderr_text = stderr.decode(encoding, errors='replace')

            # 合并输出，过滤掉 wsl 警告行
            output_lines = []
            for line in (stdout_text + stderr_text).splitlines():
                line_stripped = line.strip()
                # 过滤掉以 "wsl:" 开头的行（常见的警告）
                if line_stripped.startswith("wsl:"):
                    continue
                # 过滤掉看起来像乱码的短行（可选）
                if len(line_stripped) > 1:
                    output_lines.append(line_stripped)

            output = "\n".join(output_lines)
            return output if output else "(no output)"

        except Exception as e:
            return f"Error executing command: {str(e)}"