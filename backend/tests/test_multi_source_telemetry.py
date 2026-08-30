from decimal import Decimal
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters import (
    AssetInventoryAdapter,
    AssetInventorySimulator,
    CSPMAdapter,
    CSPMSimulator,
    EDRAdapter,
    EDRSimulator,
    IAMAdapter,
    IAMSimulator,
    SIEMAdapter,
    SIEMSimulator,
)
from app.database import Base, get_db
from app.main import app
from app.models import (
    Asset,
    BusinessService,
    CspmFinding,
    CveCatalogRecord,
    EdrEvent,
    SecurityEvent,
    User,
    UserAssetAccess,
    Vulnerability,
)
from app.services.ingestion import NormalizedIngestionService
from seed import seed


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        app.dependency_overrides.clear()


# 1. Asset Inventory Adapter & Simulator Tests
def test_asset_inventory_adapter_and_simulator(db_session):
    # Configurable simulator count
    raw_assets = AssetInventorySimulator.generate(count=15)
    assert len(raw_assets) == 15
    assert raw_assets[0]["asset_id_code"] == "GATEWAY-01"
    assert raw_assets[1]["asset_id_code"] == "PAYMENT-API-01"

    adapter = AssetInventoryAdapter()
    normalized = adapter.normalize(raw_assets)
    assert len(normalized) == 15
    assert normalized[1]["criticality"] == "CRITICAL"
    assert normalized[1]["business_value"] == Decimal("48000000.00")
    assert normalized[1]["internet_exposed"] is True

    validated = adapter.validate(normalized)
    assert len(validated) == 15

    ingested = adapter.ingest(db_session, count=15)
    assert ingested == 15
    db_asset = db_session.query(Asset).filter_by(asset_id_code="PAYMENT-API-01").one()
    assert db_asset.name == "Payment API"
    assert db_asset.cloud_provider == "AWS"


# 2. IAM Adapter & Simulator Tests
def test_iam_adapter_and_simulator(db_session):
    # Create target asset first for foreign key resolution
    asset_adapter = AssetInventoryAdapter()
    asset_adapter.ingest(db_session, count=10)

    raw_users = IAMSimulator.generate(count=10)
    assert len(raw_users) == 10
    admin_u = raw_users[0]
    assert admin_u["user_id_code"] == "USR-001"
    assert admin_u["username"] == "admin.singh"
    assert admin_u["mfa_enabled"] is False
    assert admin_u["failed_login_count"] == 17
    assert admin_u["risky_login"] is True

    adapter = IAMAdapter()
    normalized = adapter.normalize(raw_users)
    assert normalized[0]["privilege_level"] == "critical"
    assert normalized[0]["privileged"] is True

    ingested = adapter.ingest(db_session, count=10)
    assert ingested == 10

    user_in_db = db_session.query(User).filter_by(user_id_code="USR-001").one()
    assert user_in_db.display_name == "Admin Singh"
    assert len(user_in_db.asset_accesses) >= 1

    access = user_in_db.asset_accesses[0]
    assert access.access_level == "admin"
    assert access.asset is not None


# 3. SIEM Adapter & Simulator Tests
def test_siem_adapter_and_simulator(db_session):
    AssetInventoryAdapter().ingest(db_session, count=10)
    IAMAdapter().ingest(db_session, count=10)

    raw_events = SIEMSimulator.generate(count=20)
    assert len(raw_events) == 20
    assert raw_events[0]["event_type"] == "BRUTE_FORCE"
    assert raw_events[0]["technique"] == "T1110"

    adapter = SIEMAdapter()
    normalized = adapter.normalize(raw_events)
    assert normalized[0]["severity"] == "critical"
    assert normalized[0]["source"] == "SIEM"

    ingested = adapter.ingest(db_session, count=20)
    assert ingested == 20

    bf_event = db_session.query(SecurityEvent).filter_by(event_id_code="SIEM-001").one()
    assert bf_event.event_type == "BRUTE_FORCE"
    assert bf_event.source_ip == "185.10.20.30"
    assert bf_event.asset is not None
    assert bf_event.asset.asset_id_code == "PAYMENT-API-01"


# 4. EDR Adapter & Simulator Tests
def test_edr_adapter_and_simulator(db_session):
    AssetInventoryAdapter().ingest(db_session, count=10)
    IAMAdapter().ingest(db_session, count=10)

    raw_edr = EDRSimulator.generate(count=15)
    assert len(raw_edr) == 15
    assert raw_edr[0]["indicator"] == "credential_dumping"

    adapter = EDRAdapter()
    normalized = adapter.normalize(raw_edr)
    assert normalized[0]["process_name"] == "powershell.exe"

    ingested = adapter.ingest(db_session, count=15)
    assert ingested == 15

    dump_event = db_session.query(EdrEvent).filter_by(event_id_code="EDR-001").one()
    assert dump_event.indicator == "credential_dumping"
    assert dump_event.severity == "critical"
    assert dump_event.asset is not None
    assert dump_event.asset.asset_id_code == "PAYMENT-API-01"


# 5. CSPM Adapter & Simulator Tests
def test_cspm_adapter_and_simulator(db_session):
    AssetInventoryAdapter().ingest(db_session, count=10)

    raw_cspm = CSPMSimulator.generate(count=15)
    assert len(raw_cspm) == 15
    assert raw_cspm[0]["finding_type"] == "PUBLIC_S3_BUCKET"

    adapter = CSPMAdapter()
    normalized = adapter.normalize(raw_cspm)
    assert normalized[0]["internet_exposed"] is True
    assert normalized[0]["encrypted"] is False

    ingested = adapter.ingest(db_session, count=15)
    assert ingested == 15

    finding = db_session.query(CspmFinding).filter_by(finding_id_code="CSPM-001").one()
    assert finding.resource_type == "S3"
    assert finding.severity == "critical"
    assert finding.asset is not None
    assert finding.asset.asset_id_code == "S3-CUSTOMER-DATA"


# 6. Enterprise Ingestion Orchestrator Test
def test_enterprise_sync_pipeline(db_session):
    service = NormalizedIngestionService()
    result = service.sync_enterprise(
        db_session,
        asset_count=20,
        user_count=10,
        siem_count=25,
        edr_count=15,
        cspm_count=10,
    )

    assert result["assets_count"] == 20
    assert result["iam_users_count"] == 10
    assert result["iam_access_count"] >= 10
    assert result["siem_events_count"] == 25
    assert result["edr_events_count"] == 15
    assert result["cspm_findings_count"] == 10
    assert result["high_risk_scenario_confirmed"] is True


# 7. Cross-Source Asset Correlation Test (Tracing PAYMENT-API-01 across all sources)
def test_cross_source_asset_correlation(db_session):
    # Seed full deterministic scenario
    seed(db_session, asset_count=50, user_count=20, siem_count=50, edr_count=30, cspm_count=20)

    pay_asset = db_session.query(Asset).filter_by(asset_id_code="PAYMENT-API-01").one()
    assert pay_asset.criticality == "CRITICAL"
    assert pay_asset.internet_exposed is True
    assert pay_asset.business_value == Decimal("48000000.00")

    # 1. NVD / KEV Vulnerabilities
    vulns = pay_asset.vulnerabilities
    assert len(vulns) >= 1
    cve_ids = [v.cve_id for v in vulns]
    assert "CVE-2024-3094" in cve_ids or "CVE-2021-44228" in cve_ids

    # 2. IAM Authorized Users & Misconfiguration
    authorized_users = [access.user for access in pay_asset.iam_accesses]
    admin_u = next((u for u in authorized_users if u.user_id_code == "USR-001"), None)
    assert admin_u is not None
    assert admin_u.username == "admin.singh"
    assert admin_u.privileged is True
    assert admin_u.mfa_enabled is False
    assert admin_u.failed_login_count >= 10

    # 3. SIEM Telemetry
    siem_events = pay_asset.security_events
    assert len(siem_events) >= 1
    bf = next((e for e in siem_events if e.event_type == "BRUTE_FORCE"), None)
    assert bf is not None
    assert bf.technique == "T1110"
    assert bf.source_ip == "185.10.20.30"

    # 4. EDR Telemetry
    edr_events = pay_asset.edr_events
    assert len(edr_events) >= 1
    cred_dump = next((e for e in edr_events if e.indicator == "credential_dumping"), None)
    assert cred_dump is not None
    assert cred_dump.process_name == "powershell.exe"

    # 5. CSPM Findings
    cspm_findings = pay_asset.cspm_findings
    assert len(cspm_findings) >= 1
    open_sg = next((f for f in cspm_findings if f.finding_type == "OPEN_SECURITY_GROUP"), None)
    assert open_sg is not None
    assert open_sg.severity == "critical"


# 8. REST API Endpoints Test
def test_api_multi_source_endpoints(client, db_session):
    # Sync enterprise data via endpoint
    sync_resp = client.post("/api/ingestion/sync-enterprise?asset_count=25&user_count=15&siem_count=30&edr_count=15&cspm_count=10")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["assets_count"] == 25
    assert sync_data["iam_users_count"] == 15
    assert sync_data["high_risk_scenario_confirmed"] is True

    # Associate CVE-2024-21762 with PAYMENT-API-01
    pay_asset = db_session.query(Asset).filter_by(asset_id_code="PAYMENT-API-01").one()
    client.post(
        "/api/vulnerabilities/associate",
        json={"cve_id": "CVE-2024-21762", "asset_id": pay_asset.id, "status": "open"},
    )

    # 1. GET /api/assets
    assets_resp = client.get("/api/assets?criticality=CRITICAL&internet_exposed=true")
    assert assets_resp.status_code == 200
    assets = assets_resp.json()
    assert any(a["asset_id_code"] == "PAYMENT-API-01" for a in assets)

    # 2. GET /api/security-events
    siem_resp = client.get("/api/security-events?event_type=BRUTE_FORCE")
    assert siem_resp.status_code == 200
    events = siem_resp.json()
    assert len(events) >= 1
    assert events[0]["technique"] == "T1110"

    # 3. GET /api/iam/users
    users_resp = client.get("/api/iam/users?risky_login=true")
    assert users_resp.status_code == 200
    risky_users = users_resp.json()
    assert any(u["user_id_code"] == "USR-001" for u in risky_users)

    # 4. GET /api/iam/access
    access_resp = client.get("/api/iam/access?access_level=admin")
    assert access_resp.status_code == 200
    access_list = access_resp.json()
    assert len(access_list) >= 1

    # 5. GET /api/edr/events
    edr_resp = client.get("/api/edr/events?indicator=credential_dumping")
    assert edr_resp.status_code == 200
    edr_list = edr_resp.json()
    assert len(edr_list) >= 1
    assert edr_list[0]["process_name"] == "powershell.exe"

    # 6. GET /api/cspm/findings
    cspm_resp = client.get("/api/cspm/findings?severity=critical")
    assert cspm_resp.status_code == 200
    cspm_list = cspm_resp.json()
    assert len(cspm_list) >= 1

    # 7. GET /api/correlation/asset/{asset_identifier} (360° Correlated View)
    corr_resp = client.get(f"/api/correlation/asset/PAYMENT-API-01")
    assert corr_resp.status_code == 200
    corr_data = corr_resp.json()
    assert corr_data["asset"]["asset_id_code"] == "PAYMENT-API-01"
    assert len(corr_data["vulnerabilities"]) >= 1
    assert len(corr_data["security_events"]) >= 1
    assert len(corr_data["edr_events"]) >= 1
    assert len(corr_data["cspm_findings"]) >= 1
    assert len(corr_data["authorized_users"]) >= 1
    assert corr_data["composite_risk_summary"]["is_high_risk_attack_target"] is True


# 9. Seed Full Integrity Test (100 assets, 35 users, 120 SIEM, 60 EDR, 35 CSPM)
def test_seed_full_enterprise_dataset(db_session):
    seed(db_session, asset_count=100, user_count=35, siem_count=120, edr_count=60, cspm_count=35)

    assert db_session.query(Asset).count() == 100
    assert db_session.query(User).count() >= 35
    assert db_session.query(UserAssetAccess).count() >= 35
    assert db_session.query(SecurityEvent).count() == 120
    assert db_session.query(EdrEvent).count() == 60
    assert db_session.query(CspmFinding).count() == 35
    assert db_session.query(CveCatalogRecord).count() == 5
    assert db_session.query(Vulnerability).count() >= 4
