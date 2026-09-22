import hashlib
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models import AuditLog, MediaAsset, MediaVersion


@pytest.mark.asyncio
async def test_upload_media():
    content = b"SpectraX forensic test evidence"
    expected_sha256 = hashlib.sha256(content).hexdigest()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        case_response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Media Upload Test",
                "description": "Testing forensic media intake.",
            },
        )

        assert case_response.status_code == 201

        case_id = case_response.json()["id"]

        response = await client.post(
            f"/api/v1/cases/{case_id}/media",
            files={
                "file": (
                    "evidence.txt",
                    content,
                    "text/plain",
                )
            },
            data={
                "description": "Test evidence file",
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert uuid.UUID(data["asset"]["id"])
    assert data["asset"]["case_id"] == case_id
    assert data["asset"]["original_filename"] == "evidence.txt"
    assert data["asset"]["mime_type"] == "text/plain"
    assert data["asset"]["file_size"] == len(content)
    assert data["asset"]["sha256"] == expected_sha256
    assert data["asset"]["status"] == "ingested"

    assert uuid.UUID(data["version"]["id"])
    assert data["version"]["media_asset_id"] == data["asset"]["id"]
    assert data["version"]["version_number"] == 1
    assert data["version"]["sha256"] == expected_sha256
    assert data["version"]["file_size"] == len(content)


@pytest.mark.asyncio
async def test_upload_media_case_not_found():
    missing_case_id = uuid.uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/cases/{missing_case_id}/media",
            files={
                "file": (
                    "evidence.txt",
                    b"missing case test",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


@pytest.mark.asyncio
async def test_upload_empty_media():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        case_response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Empty Media Test",
                "description": "Testing empty upload rejection.",
            },
        )

        assert case_response.status_code == 201

        case_id = case_response.json()["id"]

        response = await client.post(
            f"/api/v1/cases/{case_id}/media",
            files={
                "file": (
                    "empty.txt",
                    b"",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty"


@pytest.mark.asyncio
async def test_upload_creates_audit_log():
    content = b"Audit evidence"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        case_response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Audit Media Test",
                "description": "Testing media audit trail.",
            },
        )

        assert case_response.status_code == 201

        case_id = case_response.json()["id"]

        response = await client.post(
            f"/api/v1/cases/{case_id}/media",
            files={
                "file": (
                    "audit.txt",
                    content,
                    "text/plain",
                )
            },
        )

    assert response.status_code == 201

    asset_id = response.json()["asset"]["id"]

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AuditLog)
            .where(
                AuditLog.case_id == uuid.UUID(case_id),
                AuditLog.action == "MEDIA_UPLOADED",
            )
            .order_by(AuditLog.created_at.desc())
        )

        audit_log = result.scalars().first()

    assert audit_log is not None
    assert audit_log.details["media_asset_id"] == asset_id
    assert audit_log.details["original_filename"] == "audit.txt"


@pytest.mark.asyncio
async def test_upload_creates_database_records():
    content = b"Database evidence"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        case_response = await client.post(
            "/api/v1/cases",
            json={
                "title": "Database Media Test",
                "description": "Testing media database records.",
            },
        )

        case_id = case_response.json()["id"]

        response = await client.post(
            f"/api/v1/cases/{case_id}/media",
            files={
                "file": (
                    "database.txt",
                    content,
                    "text/plain",
                )
            },
        )

    assert response.status_code == 201

    asset_id = uuid.UUID(response.json()["asset"]["id"])
    version_id = uuid.UUID(response.json()["version"]["id"])

    async with AsyncSessionLocal() as db:
        asset = await db.get(MediaAsset, asset_id)
        version = await db.get(MediaVersion, version_id)

    assert asset is not None
    assert version is not None
    assert version.media_asset_id == asset.id
    assert version.version_number == 1
