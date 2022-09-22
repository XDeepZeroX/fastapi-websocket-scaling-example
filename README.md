# Пример использования WebSocket FastAPI

## Подготовка

```
pip install -r requirements.txt
```

## Broadcast

Рассылка сообщений всем подключенным клиентам.

<u><b>НЕ</b></u> масштабируется.
Данный подход подходит только для одной реплики приложения, иначе рассылка будет работать не на всех пользователей
системы, а только на пул подключений развернутой реплики.

**Run:**

```
uvicorn main_simple:app --reload --port 8000
```

**Open:**
http://127.0.0.1:8000/

## Scaling

Для масштабирования была выбрана технология [Redis Pub/Sub](https://redis.io/docs/manual/pubsub/).

**Run:**

```
uvicorn main_redis:app --reload --port 8000
uvicorn main_redis:app --reload --port 8001
```

**Open:**

- Replica 1 - http://127.0.0.1:8000/
- Replica 2 - http://127.0.0.1:8001/

Рассылка уведомлений производится на всех пользователей, независимо к какой реплике они подключены.


