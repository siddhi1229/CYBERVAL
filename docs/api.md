# CYBERVAL Platform API

Run the API with `uvicorn app.main:app --app-dir backend --reload`, then open `http://localhost:8000/docs` for the generated OpenAPI documentation.

## Multi-Source Security Data Ingestion & Normalization Architecture (P1)

```text
NVD ──────────────────────────┐
CISA KEV ─────────────────────┤
                              │
SIEM Simulator / Connector ───┤
IAM Simulator / Connector ────┤
EDR Simulator / Connector ────┤
CSPM Simulator / Connector ───┤
Asset Inventory ──────────────┤
                              ↓
                      P1 NORMALIZATION
                              ↓
                         PostgreSQL
                              ↓
                        ┌─────┴─────┐
                        ↓           ↓
                       P2          P3
```

---

## API Endpoints

### 1. Ingestion & Multi-Source Synchronization
- `POST /api/ingestion/sync-enterprise`: Orchestrated multi-source sync (Asset Inventory $\rightarrow$ IAM $\rightarrow$ SIEM $\rightarrow$ EDR $\rightarrow$ CSPM $\rightarrow$ PostgreSQL).
- `POST /api/ingestion/sync-all`: Fetches NVD API 2.0 & CISA KEV catalog feeds, correlates into master `cve_catalog`, and enriches asset vulnerabilities.
- `POST /api/ingestion/cisa-kev/sync`: Targeted CISA KEV catalog sync.
- `POST /api/ingestion/nvd/sync`: Targeted NVD API 2.0 CVE query and catalog sync.
- `POST /api/ingestion/assets/sync`: Ingest/sync enterprise asset inventory (`count` parameter).
- `POST /api/ingestion/iam/sync`: Ingest/sync enterprise IAM identities and asset access permissions.
- `POST /api/ingestion/siem/sync`: Ingest/sync SIEM security event telemetry.
- `POST /api/ingestion/edr/sync`: Ingest/sync EDR endpoint telemetry.
- `POST /api/ingestion/cspm/sync`: Ingest/sync CSPM cloud misconfiguration findings.
- `POST /api/ingestion`: Direct ingestion endpoint accepting batches for `asset_inventory`, `iam`, `siem`, `edr`, `cspm`, `vulnerability_scanner`, `nvd`, `cisa_kev`, or `cve_catalog`.

### 2. Assets & Telemetry Queries
- `GET /api/assets`: List normalized assets (filters: `criticality`, `asset_type`, `internet_exposed`, `department`, `limit`).
- `GET /api/security-events`: List SIEM events (filters: `asset_id`, `severity`, `event_type`, `source`, `technique`, `limit`).
- `GET /api/iam/users`: List enterprise users (filters: `privilege_level`, `privileged`, `mfa_enabled`, `risky_login`, `department`, `limit`).
- `GET /api/iam/access`: List user-asset access graph (filters: `user_id`, `asset_id`, `access_level`, `limit`).
- `GET /api/edr/events`: List EDR endpoint events (filters: `endpoint_id`, `asset_id`, `event_type`, `indicator`, `severity`, `limit`).
- `GET /api/cspm/findings`: List CSPM posture findings (filters: `resource_id`, `resource_type`, `finding_type`, `severity`, `internet_exposed`, `limit`).

### 3. Vulnerability Intelligence & Correlation
- `GET /api/vulnerabilities/catalog`: Search master CVE catalog (filters: `query`, `known_exploited`, `min_cvss`, `limit`).
- `GET /api/vulnerabilities/catalog/{cve_id}`: Retrieve single normalized CVE entry.
- `POST /api/vulnerabilities/associate`: Link a catalog CVE with an asset to calculate composite risk signals.
- `GET /api/vulnerabilities`: List enriched asset vulnerabilities (filters: `known_exploited`, `internet_exposed`, `severity`).
- `GET /api/correlation/asset/{asset_identifier}`: **360-degree security correlation view for an asset** across Asset Inventory, NVD/KEV Vulnerabilities, SIEM Events, EDR Telemetry, CSPM Findings, and IAM Authorized Users.

### 4. Risk & Platform Services
- `GET /health`
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

---

All non-health endpoints read from PostgreSQL. Their request and response models are defined in `backend/app/schemas/contracts.py`. Detailed graph and digital twin architecture is available in `docs/risk-graph.md`.
