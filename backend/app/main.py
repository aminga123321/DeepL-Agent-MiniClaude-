"""
WebSocket 服务 - 接收前端消息，调用流式 Agent，实时推送结果
"""

import json
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

sys.path.append(str(Path(__file__).parent.parent))

from app.agent.agent_factory import AgentFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent WebSocket Server")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """管理 WebSocket 连接"""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"Client connected. Session: {session_id}, Total: {len(self.active_connections)}")
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        logger.info(f"Client disconnected. Session: {session_id}, Total: {len(self.active_connections)}")
    
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Send error: {e}")
                self.disconnect(session_id)


manager = ConnectionManager()


@app.get("/")
async def get_root():
    return {"status": "Agent WebSocket Server Running", "service": "Streaming Agent"}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket 聊天端点"""
    
    await websocket.accept()
    
    # 接收初始消息获取 session_id
    try:
        init_data = await websocket.receive_json()
        session_id = init_data.get("session_id", "default")
        user_id = init_data.get("user_id", "anonymous")
        
        manager.active_connections[session_id] = websocket
        logger.info(f"Client connected. Session: {session_id}, User: {user_id}")
        
    except Exception as e:
        logger.error(f"Init error: {e}")
        await websocket.close()
        return
    
    # 定义发送消息的异步函数
    async def send_to_client(msg: dict):
        await manager.send_message(session_id, msg)
    
    # 创建 Agent 实例（每个会话独立）
    agent = AgentFactory.create(
        session_id=session_id,
        user_id=user_id,
        workdir=Path.cwd()
    )
    
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            
            if not user_message.strip():
                continue
            
            logger.info(f"Received message from {session_id}: {user_message[:50]}...")
            
            await agent.process_message(
                user_message=user_message,
                send_callback=send_to_client
            )
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"Error: {e}")
        await manager.send_message(session_id, {
            "type": "error",
            "content": str(e)
        })
        manager.disconnect(session_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)