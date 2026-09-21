import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_create_case():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Automated Test Case",
                "description": "Created by API test.",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Automated Test Case"
    assert data["description"] == "Created by API test."
    assert data["status"] == "created"
    assert data["case_number"].startswith("SPX-")
    assert uuid.UUID(data["id"])


@pytest.mark.asyncio
async def test_list_cases():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/cases")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_case():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        create_response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Get Case Test",
                "description": "Testing single case retrieval.",
            },
        )

        assert create_response.status_code == 201

        case_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/cases/{case_id}",
        )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == case_id
    assert data["title"] == "Get Case Test"


@pytest.mark.asyncio
async def test_get_case_not_found():
    missing_case_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/cases/{missing_case_id}",
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"