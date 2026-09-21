import pytest

from app.worker.tasks import execute_job


@pytest.mark.asyncio
async def test_health_check_job():
    result = await execute_job(
        "health_check",
        {"source": "unit_test"},
    )

    assert result["status"] == "completed"
    assert result["job_type"] == "health_check"
    assert result["payload"] == {"source": "unit_test"}


@pytest.mark.asyncio
async def test_unknown_job_type():
    with pytest.raises(ValueError, match="Unknown job type"):
        await execute_job(
            "unknown_job",
            {},
        )
