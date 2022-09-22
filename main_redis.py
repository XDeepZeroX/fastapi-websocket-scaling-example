import asyncio
import logging
from typing import List

import aioredis
from aioredis.client import PubSub, Redis
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocket, WebSocketDisconnect

from singleton import MetaSingleton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()


async def get_redis_pool() -> Redis:
    return await aioredis.from_url(f'redis://172.16.10.1', encoding="utf-8", decode_responses=True)


async def get_pubsub() -> PubSub:
    conn = await get_redis_pool()
    pubsub = conn.pubsub()
    return pubsub


class ConnectionManager(metaclass=MetaSingleton):
    # Подключенные клиенты к вебсокету
    connections = []
    # История сообщений
    messages = []

    def __init__(self, redis: Redis):
        self.connections: List[WebSocket] = []
        self.redis = redis

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

    async def send_message(self, message: str):
        """Обрабатывает новое сообщение"""
        print(f'Новое сообщение: "{message}"')
        if not message:
            return

        self.messages.append(message)
        # Рассылаем всем подключенным клиентам
        for client in self.connections:
            await client.send_text(message)

    async def on_new_message(self, message: str):
        """Обрабатывает новое сообщение"""
        if not message:
            return

        await self.redis.publish('chat:c', message)
        print('Сообщение отправлено в Redis')

    async def send_history(self, websocket: WebSocket):
        """Отправка истории сообщений"""
        print('Рассылка пользователям')
        for msg in self.messages:
            await websocket.send_text(msg)


@app.get('/', response_class=HTMLResponse)
async def index():
    return open('index.html', 'r', encoding='utf-8').read()


@app.websocket('/ws')
async def ws_voting_endpoint(websocket: WebSocket):
    redis = await get_redis_pool()
    manager = ConnectionManager(redis)
    await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.on_new_message(f"Client {hash(websocket)} says: {message}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        # await manager.on_new_message(f"Client {hash(websocket)} left the chat")


async def producer_handler():
    redis = await get_redis_pool()
    pubsub = await get_pubsub()
    manager = ConnectionManager(redis)

    await pubsub.subscribe("chat:c")
    # assert isinstance(channel, PubSub)
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await manager.send_message(message.get('data', ''))
    except Exception as exc:
        logger.error(exc)


@app.on_event("startup")
async def on_startup():
    producer_task = producer_handler()
    asyncio.create_task(producer_task)
