from datetime import datetime
from typing import Dict, List, TypedDict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


# TypedDict para definir a estrutura de cada conexão
class Connection(TypedDict):
    websocket: WebSocket
    client_id: str


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[Connection] = []

    async def connect(self, websocket: WebSocket, user_id: str) -> str | None:
        # Verifica se o user_id já está em uso
        if any(conn["client_id"] == user_id for conn in self.active_connections):
            await websocket.close(
                code=1008, reason="Name already in use. Please choose another name."
            )
            return None

        # Aceita a conexão se o nome for único
        await websocket.accept()
        self.active_connections.append({"websocket": websocket, "client_id": user_id})
        print(f"Client connected: {user_id}. Total: {len(self.active_connections)}")
        return user_id

    def disconnect(self, websocket: WebSocket) -> str:
        client = next(
            (c for c in self.active_connections if c["websocket"] == websocket), None
        )
        if client:
            self.active_connections.remove(client)
            print(
                f"Client disconnected: {client['client_id']}. Total: {len(self.active_connections)}"
            )
        return client["client_id"] if client else "Unknow"

    async def broadcast(self, message: Dict[str, str]) -> None:
        for connection in self.active_connections:
            await connection["websocket"].send_json(message)

    def get_contacts(self) -> List[Dict[str, object]]:
        # Lista de contatos: "Global" fixo (futuramente, adicionar usuários conectados)
        contacts = [
            {
                "id": 1,
                "name": "Global",
                "last_message": "General chat",
            },
        ]
        return contacts


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    # Caso variaveis seja None, verificando
    host = websocket.client.host if websocket.client else "unknow"
    port = websocket.client.port if websocket.client else "unknow"

    print(f"WebSocket connection attempt from {host}:{port}")
    print(f"Headers: {websocket.headers}")
    print(f"Origin: {websocket.headers.get('origin', 'N/A')}")
    print(f"Query params: {websocket.query_params}")

    user_id = websocket.query_params.get("userId")
    if not user_id:
        print("userId missing, closing connection.")
        await websocket.close(code=1008, reason="userId is required")
        return

    client_id = await manager.connect(websocket, user_id)
    if client_id is None:
        print(f"Connection rejected for userId={user_id}")
        return

    print(f"WebSocket connection accepted for userId={client_id}")
    await websocket.send_json(
        {
            "type": "contacts",
            "contacts": manager.get_contacts(),
        }
    )

    await manager.broadcast(
        {
            "type": "system",
            "text": f"{client_id} joined the chat",
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Message received from {client_id}: {data}")
            message = {
                "type": "message",
                "sender": client_id,
                "text": data,
                "timestamp": datetime.now().strftime("%H:%M"),
            }
            await manager.broadcast(message)
    except WebSocketDisconnect:
        client_id = manager.disconnect(websocket)
        print(f"WebSocket connection disconnected for {client_id}")
        await manager.broadcast(
            {
                "type": "system",
                "text": f"{client_id} left the chat",
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        )
    except Exception as e:
        print(f"WebSocket Error: {e}")
        await websocket.close(code=1011, reason=str(e))


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "Welcome to Live chat with WebSocket!"}
