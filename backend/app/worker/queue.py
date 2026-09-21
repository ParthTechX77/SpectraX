import json
from typing import Any

from redis.exceptions import TimeoutError as RedisTimeoutError

from app.redis_client import redis_client


QUEUE_NAME = "spectrax:jobs"


async def enqueue_job(
    job_type: str,
    payload: dict[str, Any],
) -> None:
    job = {
        "type": job_type,
        "payload": payload,
    }

    await redis_client.rpush(
        QUEUE_NAME,
        json.dumps(job),
    )


async def dequeue_job() -> dict[str, Any] | None:
    try:
        result = await redis_client.blpop(
            QUEUE_NAME,
            timeout=5,
        )
    except RedisTimeoutError:
        return None

    if result is None:
        return None

    _, raw_job = result

    return json.loads(raw_job)
