import json
from redis import asyncio as aioredis
from redis.exceptions import RedisError
from fastapi import HTTPException
from app.config import settings

class RedisService:
    def __init__(self):
        self.redis_url = f"redis://{':' + settings.redis_password + '@' if settings.redis_password else ''}{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        self.redis = None
        self.ttl = settings.session_ttl

    async def connect(self):
        try:
            if not self.redis:
                self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        except RedisError as e:
            raise HTTPException(status_code=500, detail=f"Redis connection error: {str(e)}")

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
            self.redis = None

    async def get_session(self, session_id: str) -> dict:
        try:
            await self.connect()
            data = await self.redis.get(f"session:{session_id}")
            return json.loads(data) if data else None
        except RedisError as e:
            raise HTTPException(status_code=500, detail=f"Redis error: {str(e)}")

    async def set_session(self, session_id: str, data: dict):
        await self.connect()
        await self.redis.setex(
            f"session:{session_id}",
            self.ttl,
            json.dumps(data)
        )

    async def delete_session(self, session_id: str):
        await self.connect()
        await self.redis.delete(f"session:{session_id}")

redis_service = RedisService() 