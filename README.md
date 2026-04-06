# DeepL-Agent

一个模仿 Claude 架构的流式 AI Agent，支持动态工具调用和多轮对话。

## 特性

- 🚀 **流式输出**：WebSocket 实时逐字输出，打字机效果
- 🔧 **工具系统**：动态注册和执行工具（Bash、文件读写、技能加载）
- 🧩 **模块化**：工具、事件处理、消息构建完全解耦
- 💬 **多轮对话**：自动管理上下文，支持复杂任务
- 🌍 **跨平台**：Windows（WSL）、Linux、macOS

## 项目结构
DeepL-Agent/
├── backend/
│ ├── app/
│ │ ├── agent/ # Agent 核心逻辑
│ │ │ ├── streaming_agent.py
│ │ │ ├── event_handler.py
│ │ │ ├── message_builder.py
│ │ │ ├── context.py
│ │ │ ├── models.py
│ │ │ └── agent_factory.py
│ │ ├── tools/ # 工具系统
│ │ │ ├── base.py
│ │ │ ├── bash.py
│ │ │ ├── read_file.py
│ │ │ ├── write_file.py
│ │ │ └── load_skill.py
│ │ ├── main.py # WebSocket 服务入口
│ │ └── skill_loader.py # 技能加载器
│ ├── skills/ # 技能文件（SKILL.md）
│ └── requirements.txt # Python 依赖
├── frontend/
│ ├── src/
│ │ ├── components/
│ │ │ └── ChatWindow.vue
│ │ └── ...
│ ├── package.json
│ └── vite.config.js
└── README.md

text

## 技术栈

| 后端 | 前端 |
|------|------|
| FastAPI | Vue 3 |
| WebSocket | TypeScript |
| Anthropic SDK | Vite |

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- Windows 用户需要 WSL 或 Git Bash

### 安装与运行

```bash
# 克隆仓库
git clone https://github.com/aminga123321/DeepL-Agent-MiniClaude-.git
cd DeepL-Agent-MiniClaude-

# 后端
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入你的 API Key
python app/main.py

# 前端（新终端）
cd frontend
npm install
npm run dev