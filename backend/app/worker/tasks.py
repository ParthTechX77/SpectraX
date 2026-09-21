from typing import Any


async def execute_job(
    job_type: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if job_type == "health_check":
        return {
            "status": "completed",
            "job_type": job_type,
            "payload": payload,
        }

    raise ValueError(f"Unknown job type: {job_type}")
