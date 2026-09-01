# CYBERVAL

CYBERVAL is an AI-powered continuous cyber risk quantification and security investment optimization platform. This repository contains the shared P1 platform foundation: PostgreSQL persistence, normalized domain entities, API contracts, synthetic seed data, and ingestion primitives.

## Using an Online / Cloud Database (Neon, Supabase, Render, AWS RDS)

CYBERVAL supports any cloud-hosted PostgreSQL database out of the box with SSL support and connection resilience:

1. Create a `.env` file in the project root (or copy from `.env.example`).
2. Add your cloud database connection string:
   ```env
   # Example with Neon Serverless Postgres:
   DATABASE_URL=postgresql+psycopg://user:password@ep-sample-123456.us-east-2.aws.neon.tech/neondb?sslmode=require

   # Example with Supabase:
   DATABASE_URL=postgresql+psycopg://postgres.xxx:password@aws-0-region.pooler.supabase.com:6543/postgres
   ```
3. Test your database connectivity:
   ```powershell
   python backend\check_db.py
   ```
4. Initialize and seed the schema:
   ```powershell
   python backend\init_db.py
   python backend\seed.py
   ```
5. Start the API server:
   ```powershell
   uvicorn app.main:app --reload --app-dir backend
   ```

## Run with Docker

```powershell
docker compose up --build
```

The API is available at `http://localhost:8000`; interactive documentation is at `http://localhost:8000/docs`.

## Run locally (Local PostgreSQL)

Use Python 3.12+ and PostgreSQL, then:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\init_db.py
python backend\seed.py
uvicorn app.main:app --reload --app-dir backend
```

See [docs/api.md](docs/api.md) for the shared endpoint contract. PostgreSQL is the only supported source of truth; modules must consume these models and APIs rather than creating parallel storage.

