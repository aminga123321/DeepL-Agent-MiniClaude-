from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
import json

from config import WORKDIR
from websocket.connection_manager import ConnectionManager
from websocket.stream_handler import StreamHandler
from core.agent_loop import agent_loop_stream
from managers.task_manager import TaskManager
from managers.teammate_manager import TeammateManager
from managers.skill_loader import SKILLS

app = FastAPI(title="Agent Backend")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/health")
async def health():
    return {"status": "ok", "workdir": str(WORKDIR)}


@app.get("/api/skills")
async def list_skills():
    """获取所有可用的 Skill 列表（用于前端命令面板）"""
    return {"skills": SKILLS.get_command_list()}


@app.get("/api/conversations/{user_id}")
async def get_conversations(user_id: str):
    """获取用户的历史对话列表（Phase 2 实现）"""
    # TODO: Phase 2 实现
    return {"conversations": []}


@app.get("/api/conversation/{user_id}/{conversation_id}")
async def get_conversation(user_id: str, conversation_id: str):
    """获取单个对话的详细内容（Phase 2 实现）"""
    # TODO: Phase 2 实现
    return {"messages": []}


@app.websocket("/ws/agent")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="用户ID")
):
    """WebSocket 端点，需要传入 user_id"""
    await manager.connect(user_id, websocket)
    handler = StreamHandler(websocket, user_id)

    # 初始化用户的消息历史
    messages = []

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "query":
                query = data.get("query", "")
                history = data.get("history", [])

                # 使用传入的历史或初始化
                if history:
                    messages = history
                messages.append({"role": "user", "content": query})

                # 运行流式 Agent
                await agent_loop_stream(messages, user_id, handler)

            elif msg_type == "clear":
                messages = []
                await handler.send_status("对话已清空")

            elif msg_type == "load_conversation":
                # 加载历史对话（Phase 2）
                pass

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        await handler.send_error(str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
