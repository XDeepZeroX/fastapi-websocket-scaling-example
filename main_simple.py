import logging
from typing import List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()


@app.get('/', response_class=HTMLResponse)
async def index():
    return open('index.html', 'r', encoding='utf-8').read()


class ConnectionManager:
    # Подключенные клиенты к вебсокету
    connections = []
    # История сообщений
    messages = []

    def __init__(self):
        self.connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        """Выполнить действие при подключении пользователя"""
        print(f'connect: {hash(websocket)}')
        self.connections.append(websocket)
        # Например, отправить историю последних сообщений...
        await self.send_history(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Обрабатывает отключение клиента"""
        print(f'Disconnect: {hash(websocket)}')
        self.connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.connections:
            await connection.send_text(message)

    async def on_new_message(self, message: str):
        """Обрабатывает новое сообщение"""
        self.messages.append(message)
        # Рассылаем всем подключенным клиентам
        for client in self.connections:
            await client.send_text(message)

    async def send_history(self, websocket: WebSocket):
        """Отправка истории сообщений"""
        for msg in self.messages:
            await websocket.send_text(msg)


manager = ConnectionManager()


@app.get('/new_message/{message}', response_class=PlainTextResponse)
async def create_message(message: str):
    # Создать новое сообщение и разослать всем клиентам
    await manager.on_new_message(message)
    return f'Сообщение: {message}\n\nДоставлено клиентам !'


@app.websocket('/ws')
async def ws_voting_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.broadcast(f"Client {hash(websocket)} says: {message}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        # await manager.broadcast(f"Client {hash(websocket)} left the chat")
