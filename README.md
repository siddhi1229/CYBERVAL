# CYBERVAL

CYBERVAL is an AI-powered continuous cyber risk quantification and security investment optimization platform. This repository contains the shared P1 platform foundation: PostgreSQL persistence, normalized domain entities, API contracts, synthetic seed data, and ingestion primitives.

## Run with Docker

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`; interactive documentation is at `http://localhost:8000/docs`.

## Run locally

Use Python 3.12 and PostgreSQL, then:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
python backend\init_db.py
python backend\seed.py
uvicorn app.main:app --reload --app-dir backend
```

See [docs/api.md](docs/api.md) for the shared endpoint contract. PostgreSQL is the only supported source of truth; modules must consume these models and APIs rather than creating parallel storage.
