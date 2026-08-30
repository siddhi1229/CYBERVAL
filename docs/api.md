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
- `GET /api/risk/enterprise` — engine-backed by P2 (see section 5)
- `GET /api/risk/assets` — engine-backed by P2 (see section 5)
- `POST /api/ai/recommend`
- `POST /api/ai/query`
- `POST /api/simulation/run`
- `POST /api/investments/optimize`
- `GET /api/compliance`

### 5. Cyber Risk Quantification Engine (P2)

Consumes P1 PostgreSQL telemetry and returns financial cyber risk. Full model,
formulas, assumptions and limitations: [`docs/risk-engine.md`](risk-engine.md).
These routes are registered ahead of the P1 router and supersede P1's
`/api/risk/enterprise` and `/api/risk/assets` stubs (P1 `routers.py` unchanged).

- `POST /api/risk/calculate`: run the engine (optional `asset_ids`, `iterations`, `persist`, `config_overrides`). With `persist=true`, upserts the P1 `risks` row per asset and appends `risk_history` snapshots.
- `GET /api/risk/assets`: financial risk for every asset (`min_score`, `business_service`, `department`, `limit`), sorted by Expected Annual Loss.
- `GET /api/risk/assets/{asset_id}`: full breakdown — risk signals, likelihood, financial-impact components, Monte Carlo distribution, control evaluations, risk drivers.
- `GET /api/risk/enterprise`: enterprise + per business-service + per-department risk, with VaR95 / VaR99.
- `GET /api/risk/drivers`: top risk drivers (`scope=enterprise` | `high_risk_assets`).
- `GET /api/risk/trends`: historical risk snapshots from `risk_history` (`scope`, `ref`, `limit`).

Response fields per asset: `risk_score` (0–100 ordinal), `likelihood_score`
(0–1 ordinal, **not** a probability), `annual_incident_probability` (0–1),
`financial_impact` (INR), `expected_annual_loss` = probability × impact,
`control_effectiveness` (0–1), `inherent`/`residual_expected_annual_loss`,
`p95_loss` (= VaR95), `p99_loss` (= VaR99), `risk_drivers`.

**Schema change (only one in P2):** new append-only `risk_history` table for
trends. No P1 table or model is modified; created via `Base.metadata.create_all`.

---

All non-health endpoints read from PostgreSQL. Their request and response models are defined in `backend/app/schemas/contracts.py`. Detailed graph and digital twin architecture is available in `docs/risk-graph.md`.
