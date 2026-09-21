import pytest

from app.redis_client import redis_client
from app.worker.queue import (
    QUEUE_NAME,
    dequeue_job,
    enqueue_job,
)


@pytest.mark.asyncio
async def test_enqueue_and_dequeue_job():
    await redis_client.aclose()

    try:
        await enqueue_job(
            "health_check",
            {"source": "queue_test"},
        )

        job = await dequeue_job()

        assert job is not None
        assert job["type"] == "health_check"
        assert job["payload"] == {"source": "queue_test"}

    finally:
        await redis_client.aclose()


@pytest.mark.asyncio
async def test_dequeue_empty_queue():
    await redis_client.aclose()

    try:
        job = await dequeue_job()

        assert job is None

    finally:
        await redis_client.aclose()
