import asyncio

from app.redis_client import redis_client
from app.worker.queue import dequeue_job
from app.worker.tasks import execute_job


async def run_worker() -> None:
    print("SpectraX worker started.")

    while True:
        job = await dequeue_job()

        if job is None:
            continue

        try:
            result = await execute_job(
                job["type"],
                job["payload"],
            )

            print(f"Job completed: {result}")

        except Exception as exc:
            print(f"Job failed: {exc}")


async def main() -> None:
    try:
        await run_worker()
    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
