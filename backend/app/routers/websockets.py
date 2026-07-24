from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

router = APIRouter(prefix="/ws", tags=["WebSockets"])
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> List of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total active sessions: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"User {user_id} disconnected.")

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connections in self.active_connections.values():
            for connection in connections:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Broadcast read receipts or typing indicators if necessary
            msg_type = message_data.get("type", "message")
            recipient_id = message_data.get("recipient_id")
            
            payload = {
                "sender_id": user_id,
                "type": msg_type,
                "content": message_data.get("content"),
                "status": "delivered"
            }
            
            if recipient_id:
                await manager.send_personal_message(payload, recipient_id)
            else:
                await manager.broadcast(payload)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        # Notify others about offline status
        await manager.broadcast({
            "sender_id": user_id,
            "type": "status",
            "content": "offline"
        })
