# SpectraX

SpectraX is a multimodal AI forensics platform for digital media analysis, deepfake detection, provenance analysis, and digital evidence workflows.

## Current Status

**Phase 0 — Foundation: Complete**

Phase 0 establishes the core development, backend, database, storage, worker, frontend integration, and testing foundation required for later forensic analysis phases.

---

## Project Structure

```text
SpectraX/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── storage/
│   │   ├── worker/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── main.py
│   │   └── redis_client.py
│   └── requirements.txt
│
├── database/
│   └── migrations/
│       └── alembic/
│
├── frontend/
│   ├── app/
│   ├── lib/
│   ├── package.json
│   └── package-lock.json
│
├── storage/
│   ├── uploads/
│   ├── extracted/
│   ├── evidence/
│   ├── reports/
│   └── temporary/
│
├── tests/
│   ├── api/
│   └── unit/
│       ├── storage/
│       └── worker/
│
├── docker-compose.yml
├── alembic.ini
├── pytest.ini
└── README.md