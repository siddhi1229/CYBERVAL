from datetime import UTC, datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models import Asset, BusinessService, CveCatalogRecord, Vulnerability
from app.services.cisa_kev import CisaKevClient
from app.services.correlator import CveCorrelatorService
from app.services.ingestion import NormalizedIngestionService
from app.services.nvd import NvdClient


@pytest.fixture
def test_db_engine():
    """Create a thread-safe in-memory SQLite database engine."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_db_engine):
    """Provide a database session for test setup & assertions."""
    Session = sessionmaker(bind=test_db_engine, autoflush=False, autocommit=False)
    session = Session()

    # Seed baseline business service & assets
    payment_svc = BusinessService(
        name="Payment Service",
        owner="Digital Commerce",
        criticality="critical",
        annual_revenue=Decimal("480000000"),
    )
    session.add(payment_svc)
    session.flush()

    gw_asset = Asset(
        name="Internet Gateway",
        asset_type="network",
        owner="Platform",
        internet_exposed=True,
        business_service=payment_svc,
    )
    api_asset = Asset(
        name="Payment API",
        asset_type="application",
        owner="Payments",
        internet_exposed=True,
        business_service=payment_svc,
    )
    db_asset = Asset(
        name="Internal DB",
        asset_type="database",
        owner="Data Team",
        internet_exposed=False,
        business_service=payment_svc,
    )
    session.add_all([gw_asset, api_asset, db_asset])
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(test_db_engine, db_session):
    """FastAPI TestClient with overridden thread-safe database session."""
    TestingSessionLocal = sessionmaker(bind=test_db_engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==========================================
# 1. NVD Client Unit Tests
# ==========================================

def test_nvd_client_parsing_and_fixtures():
    client = NvdClient()
    rec = client.fetch_cve("CVE-2024-21762")
    assert rec is not None
    assert rec["cve_id"] == "CVE-2024-21762"
    assert rec["cvss_score"] == Decimal("9.8")
    assert rec["severity"] == "CRITICAL"
    assert "fortios" in rec["affected_product"].lower()
    assert "CWE-787" in rec["cwe_ids"]


def test_nvd_client_custom_item_parsing():
    client = NvdClient()
    dummy_item = {
        "cve": {
            "id": "CVE-2025-99999",
            "descriptions": [{"lang": "en", "value": "Mock test vulnerability"}],
            "metrics": {
                "cvssMetricV31": [
                    {
                        "cvssData": {
                            "baseScore": 8.8,
                            "baseSeverity": "HIGH",
                            "vectorString": "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H",
                        }
                    }
                ]
            },
            "weaknesses": [
                {"description": [{"value": "CWE-89"}]}
            ],
            "configurations": [
                {
                    "nodes": [
                        {
                            "cpeMatch": [
                                {"criteria": "cpe:2.3:a:acme:super_gateway:1.0:*:*:*:*:*:*:*"}
                            ]
                        }
                    ]
                }
            ],
        }
    }
    parsed = client.parse_nvd_item(dummy_item)
    assert parsed["cve_id"] == "CVE-2025-99999"
    assert parsed["cvss_score"] == Decimal("8.8")
    assert parsed["severity"] == "HIGH"
    assert parsed["affected_vendor"] == "Acme"
    assert parsed["affected_product"] == "Super Gateway"
    assert parsed["cwe_ids"] == "CWE-89"


# ==========================================
# 2. CISA KEV Client Unit Tests
# ==========================================

def test_cisa_kev_client_parsing_and_fixtures():
    client = CisaKevClient()
    catalog = client.fetch_catalog()
    assert len(catalog) > 0
    fortinet_kev = next((item for item in catalog if item["cve_id"] == "CVE-2024-21762"), None)
    assert fortinet_kev is not None
    assert fortinet_kev["vendor_project"] == "Fortinet"
    assert isinstance(fortinet_kev["known_ransomware_campaign_use"], bool)
    assert "CWE-787" in fortinet_kev["cwe_ids"]

    log4shell_kev = next((item for item in catalog if item["cve_id"] == "CVE-2021-44228"), None)
    assert log4shell_kev is not None
    assert log4shell_kev["known_ransomware_campaign_use"] is True


# ==========================================
# 3. CVE Correlator Service Tests
# ==========================================

def test_cve_correlator_combines_nvd_and_kev():
    correlator = CveCorrelatorService()
    nvd_rec = correlator.nvd.fetch_cve("CVE-2024-21762")
    kev_items = correlator.kev.fetch_catalog()
    kev_rec = next(k for k in kev_items if k["cve_id"] == "CVE-2024-21762")

    result = correlator.correlate_cve("CVE-2024-21762", nvd_record=nvd_rec, kev_record=kev_rec)
    assert result["cve_id"] == "CVE-2024-21762"
    assert result["cvss_score"] == Decimal("9.8")
    assert result["severity"] == "CRITICAL"
    assert result["known_exploited"] is True
    assert result["kev_date_added"] is not None
    assert "NVD" in result["sources"]
    assert "CISA_KEV" in result["sources"]


def test_cve_correlator_nvd_only():
    correlator = CveCorrelatorService()
    nvd_rec = correlator.nvd.fetch_cve("CVE-2024-3094")
    result = correlator.correlate_cve("CVE-2024-3094", nvd_record=nvd_rec, kev_record=None)
    assert result["cve_id"] == "CVE-2024-3094"
    assert result["cvss_score"] == Decimal("10.0")
    assert result["severity"] == "CRITICAL"
    assert result["known_exploited"] is False
    assert result["sources"] == "NVD"


def test_asset_vulnerability_association_and_risk_signal(db_session):
    correlator = CveCorrelatorService()
    gw_asset = db_session.query(Asset).filter_by(name="Internet Gateway").one()

    vuln = correlator.associate_cve_with_asset(
        db_session,
        cve_id="CVE-2024-21762",
        asset_id=gw_asset.id,
    )
    assert vuln.cve_id == "CVE-2024-21762"
    assert vuln.cvss_score == Decimal("9.8")
    assert vuln.known_exploited is True
    # Internet Gateway is internet_exposed=True and payment_svc is criticality="critical"
    assert vuln.composite_risk_priority == "CRITICAL_EXPLOITED_EXPOSED"


def test_sync_catalog_and_enrich_pipeline(db_session):
    correlator = CveCorrelatorService()
    gw_asset = db_session.query(Asset).filter_by(name="Internet Gateway").one()

    # Create raw placeholder vulnerability
    raw_vuln = Vulnerability(
        cve_id="CVE-2024-21762",
        title="Unenriched Fortinet Bug",
        cvss_score=Decimal("0.0"),
        severity="unknown",
        asset_id=gw_asset.id,
    )
    db_session.add(raw_vuln)
    db_session.commit()

    # Sync catalog
    kev_cnt, nvd_cnt, cat_cnt = correlator.sync_catalog(db_session, cve_ids=["CVE-2024-21762"], sync_cisa_kev=True, sync_nvd=True)
    assert cat_cnt >= 1

    # Enrich asset vulnerabilities
    enriched = correlator.enrich_asset_vulnerabilities(db_session)
    assert enriched >= 1

    db_session.refresh(raw_vuln)
    assert raw_vuln.cvss_score == Decimal("9.8")
    assert raw_vuln.known_exploited is True
    assert raw_vuln.severity == "critical"
    assert raw_vuln.composite_risk_priority == "CRITICAL_EXPLOITED_EXPOSED"


# ==========================================
# 4. Ingestion Service Telemetry Tests
# ==========================================

def test_ingestion_service_with_telemetry_sources(db_session):
    service = NormalizedIngestionService()
    api_asset = db_session.query(Asset).filter_by(name="Payment API").one()

    # Ingest CVE catalog item directly
    cve_records = [
        {
            "cve_id": "CVE-2023-4966",
            "title": "Citrix Bleed",
            "cvss_score": 9.4,
            "severity": "CRITICAL",
            "known_exploited": True,
            "affected_product": "NetScaler",
        }
    ]
    service.ingest(db_session, "cve_catalog", cve_records)
    cat_entry = db_session.get(CveCatalogRecord, "CVE-2023-4966")
    assert cat_entry is not None
    assert cat_entry.known_exploited is True

    # Ingest vulnerability scanner finding - automatically enriched via catalog!
    scanner_records = [
        {
            "cve_id": "CVE-2023-4966",
            "asset_id": api_asset.id,
        }
    ]
    count = service.ingest(db_session, "vulnerability_scanner", scanner_records)
    assert count == 1

    vuln = db_session.query(Vulnerability).filter_by(cve_id="CVE-2023-4966", asset_id=api_asset.id).one()
    assert vuln.known_exploited is True
    assert vuln.cvss_score == Decimal("9.4")
    assert vuln.composite_risk_priority == "CRITICAL_EXPLOITED_EXPOSED"


# ==========================================
# 5. REST API Integration Tests
# ==========================================

def test_api_catalog_and_association(client, db_session):
    gw_asset = db_session.query(Asset).filter_by(name="Internet Gateway").one()

    # 1. Sync all
    sync_resp = client.post("/api/ingestion/sync-all", json={"cve_ids": ["CVE-2024-21762", "CVE-2024-3094"]})
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["correlated_catalog_count"] >= 2

    # 2. Get catalog
    cat_resp = client.get("/api/vulnerabilities/catalog?known_exploited=true")
    assert cat_resp.status_code == 200
    catalog = cat_resp.json()
    assert any(c["cve_id"] == "CVE-2024-21762" for c in catalog)

    # 3. Associate CVE with Asset
    assoc_resp = client.post(
        "/api/vulnerabilities/associate",
        json={
            "cve_id": "CVE-2024-21762",
            "asset_id": gw_asset.id,
            "status": "open",
        },
    )
    assert assoc_resp.status_code == 200
    assoc_data = assoc_resp.json()
    assert assoc_data["cve_id"] == "CVE-2024-21762"
    assert Decimal(str(assoc_data["cvss_score"])) == Decimal("9.8")
    assert assoc_data["known_exploited"] is True
    assert assoc_data["internet_exposed"] is True
    assert assoc_data["business_service_criticality"] == "critical"
    assert assoc_data["composite_risk_priority"] == "CRITICAL_EXPLOITED_EXPOSED"

    # 4. List vulnerabilities with filters
    list_resp = client.get("/api/vulnerabilities?known_exploited=true&internet_exposed=true")
    assert list_resp.status_code == 200
    vulns = list_resp.json()
    assert len(vulns) >= 1
    assert vulns[0]["cve_id"] == "CVE-2024-21762"
