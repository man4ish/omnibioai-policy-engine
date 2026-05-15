import asyncio
import json
import os
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from app.api.routes_policy import router
from app.services.cache import PolicyCache

_redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
_cache = PolicyCache(redis_url=_redis_url)


async def _invalidation_subscriber():
    """
    Subscribe to "policy:invalidate" pub/sub channel.
    On each message, evict the affected user's cached policy decisions so
    the next request re-evaluates from scratch (zero-trust on revocation).
    Restarts automatically on failure.
    """
    client = aioredis.from_url(_redis_url, decode_responses=True)
    while True:
        try:
            pubsub = client.pubsub()
            await pubsub.subscribe("policy:invalidate")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        user_id = data.get("user_id", "")
                        if user_id:
                            _cache.invalidate_user(user_id)
                    except Exception:
                        pass
        except Exception:
            await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_invalidation_subscriber())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="OmniBioAI Policy Engine", lifespan=lifespan)

app.include_router(router, prefix="/policy")
