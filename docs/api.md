# CYBERVAL Platform API

Run the API with `uvicorn app.main:app --app-dir backend --reload`, then open `http://localhost:8000/docs` for the generated OpenAPI documentation.

## Contract

- `GET /health`
- `GET /api/assets`
- `GET /api/vulnerabilities`
- `GET /api/threats`
- `GET /api/controls`
- `GET /api/graph`
- `GET /api/attack-paths`
- `GET /api/assets/{asset_id}/dependencies`
- `GET /api/assets/{asset_id}/attack-paths`
- `GET /api/correlation/asset/{asset_id}`
- `GET /api/risk/enterprise`
- `GET /api/risk/assets`
- `POST /api/ai/recommend`
- `POST /api/ai/query`
- `POST /api/simulation/run`
- `POST /api/investments/optimize`
- `GET /api/compliance`
- `POST /api/ingestion`

`POST /api/ingestion` accepts a `source` of `vulnerability_scanner`, `siem`, `iam`, `edr`, `cspm`, `asset_inventory`, or `threat_intelligence`, plus a list of normalized source records. The ingestion service writes directly to the shared PostgreSQL entities.

All non-health endpoints read from PostgreSQL. Their request and response models are defined in `backend/app/schemas/contracts.py`. Detailed graph and digital twin architecture is available in `docs/risk-graph.md`.
