@echo off
echo 🚀 启动 GitHub Trends MCP Server...
echo 📅 时间: %date% %time%
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖
if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

echo 📦 激活虚拟环境...
call venv\Scripts\activate.bat

echo 📦 安装依赖...
pip install -r requirements.txt

echo 🚀 启动服务器...
python github_trends_mcp.py

pause