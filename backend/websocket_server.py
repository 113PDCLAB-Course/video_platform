import asyncio
import datetime
import json
import websockets
from typing import Set, Dict
from config import settings

class WebSocketServer:
    def __init__(self):
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.users: Dict[str, websockets.WebSocketServerProtocol] = {}

    async def register(self, websocket: websockets.WebSocketServerProtocol, user_id: str):
        self.connections.add(websocket)
        self.users[user_id] = websocket

    async def unregister(self, websocket: websockets.WebSocketServerProtocol, user_id: str):
        self.connections.remove(websocket)
        self.users.pop(user_id, None)

    async def broadcast(self, message: dict):
        if self.connections:
            await asyncio.gather(
                *[conn.send(json.dumps(message)) for conn in self.connections]
            )

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.users:
            await self.users[user_id].send(json.dumps(message))

    async def handler(self, websocket: websockets.WebSocketServerProtocol, path: str):
        user_id = path.split('/')[-1]
        await self.register(websocket, user_id)
        try:
            async for message in websocket:
                data = json.loads(message)
                if data['type'] == 'chat':
                    await self.broadcast({
                        'type': 'chat',
                        'user_id': user_id,
                        'message': data['message'],
                        'timestamp': datetime.utcnow().isoformat()
                    })
                elif data['type'] == 'notification':
                    target_user_id = data['target_user_id']
                    await self.send_to_user(target_user_id, {
                        'type': 'notification',
                        'message': data['message']
                    })
        finally:
            await self.unregister(websocket, user_id)