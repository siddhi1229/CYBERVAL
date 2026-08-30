import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Setup test SQLite database
os.environ["DATABASE_URL"] = "sqlite:///./test_cyberval.db"

from app.database import Base, get_db
from app.main import app
from app.models import (
    Asset, BusinessService, Control, FrameworkControl, Investment, Risk,
    SecurityEvent, Threat, User, Vulnerability,
)
from app.services.graph_service import CyberRiskDigitalTwin
from seed import seed

TEST_DB_URL = "sqlite:///./test_cyberval.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables and seed the full enterprise dataset once for tests."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as session:
        seed(session)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_cyberval.db"):
        try:
            os.remove("test_cyberval.db")
        except Exception:
            pass


@pytest.fixture
def db_session():
    with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


# ==========================================
# 1. Database Seeding & Models Verification
# ==========================================

def test_enterprise_dataset_seeded(db_session: Session):
    """Verify that the database contains the realistic enterprise dataset."""
    assets = db_session.scalars(select(Asset)).all()
    assert len(assets) == 100, f"Expected 100 assets, found {len(assets)}"

    users = db_session.scalars(select(User)).all()
    assert len(users) == 35, f"Expected 35 users, found {len(users)}"

    services = db_session.scalars(select(BusinessService)).all()
    assert len(services) == 5, f"Expected 5 business services, found {len(services)}"

    controls = db_session.scalars(select(Control)).all()
    assert len(controls) == 8, f"Expected 8 controls, found {len(controls)}"

    threats = db_session.scalars(select(Threat)).all()
    assert len(threats) == 5, f"Expected 5 threats, found {len(threats)}"

    events = db_session.scalars(select(SecurityEvent)).all()
    siem_events = [e for e in events if e.source == "siem"]
    edr_events = [e for e in events if e.source == "edr"]
    cspm_events = [e for e in events if e.source == "cspm"]
    iam_events = [e for e in events if e.source == "iam"]

    assert len(siem_events) >= 120, f"Expected >= 120 SIEM events, found {len(siem_events)}"
    assert len(edr_events) >= 60, f"Expected >= 60 EDR events, found {len(edr_events)}"
    assert len(cspm_events) >= 35, f"Expected >= 35 CSPM findings, found {len(cspm_events)}"
    assert len(iam_events) >= 50, f"Expected >= 50 IAM mappings, found {len(iam_events)}"


# ==========================================
# 2. Correlated Scenario: PAYMENT-API-01
# ==========================================

def test_payment_api_01_correlation(db_session: Session):
    """
    Test the multi-source correlation specifically for PAYMENT-API-01:
    - CVE-2024-21762
    - Internet exposed
    - Privileged IAM access without MFA
    - SIEM brute force (T1110)
    - EDR credential dumping (T1003)
    - CSPM open security group
    - Payment Service (critical)
    """
    payment_api = db_session.scalar(select(Asset).where(Asset.name == "PAYMENT-API-01"))
    assert payment_api is not None
    assert payment_api.internet_exposed is True
    assert payment_api.business_service is not None
    assert payment_api.business_service.criticality == "critical"

    digital_twin = CyberRiskDigitalTwin(db_session)
    correlation = digital_twin.correlate_asset_sources("PAYMENT-API-01")

    assert correlation is not None
    assert correlation.asset_name == "PAYMENT-API-01"
    assert correlation.internet_exposed is True
    assert correlation.business_service == "Payment Service"
    assert correlation.converged_risk_level == "critical"
    assert correlation.graph_risk_score >= 90.0

    # Verify vulnerabilities
    cves = [v["cve_id"] for v in correlation.vulnerabilities]
    assert "CVE-2024-21762" in cves

    # Verify SIEM
    siem_types = [e["event_type"] for e in correlation.siem_events]
    assert any("Brute Force" in st for st in siem_types)

    # Verify EDR
    edr_types = [e["event_type"] for e in correlation.edr_events]
    assert any("Credential Dumping" in et for et in edr_types)

    # Verify CSPM
    cspm_types = [c["event_type"] for c in correlation.cspm_findings]
    assert any("Open Security Group" in ct for ct in cspm_types)

    # Verify IAM
    assert len(correlation.iam_access) > 0

    # Verify risk factors list contains multi-signal converged warnings
    assert len(correlation.risk_factors) >= 4


# ==========================================
# 3. Digital Twin Graph Construction & Cytoscape
# ==========================================

def test_graph_construction_and_cytoscape(db_session: Session):
    """Verify that the NetworkX digital twin builds with all required node types and edge semantics."""
    digital_twin = CyberRiskDigitalTwin(db_session)
    cy_data = digital_twin.get_cytoscape_data()

    assert len(cy_data.nodes) > 0
    assert len(cy_data.edges) > 0

    node_types = set(n.data.type for n in cy_data.nodes)
    expected_types = {"Asset", "Vulnerability", "User", "Threat", "Control", "BusinessService", "SecurityEvent", "EDREvent", "CSPMFinding", "EntryZone"}
    for exp in expected_types:
        assert exp in node_types, f"Missing node type {exp} in digital twin graph"

    edge_rels = set(e.data.relationship for e in cy_data.edges)
    expected_rels = {"HAS_ACCESS", "HAS_VULNERABILITY", "PROTECTED_BY", "PART_OF", "DEPENDS_ON", "CONNECTS_TO", "OBSERVED_ON", "AFFECTS", "EXPLOITS"}
    for rel in expected_rels:
        assert rel in edge_rels, f"Missing edge relationship {rel} in digital twin graph"

    # Verify summary statistics
    assert cy_data.summary is not None
    assert cy_data.summary.total_nodes == len(cy_data.nodes)
    assert cy_data.summary.total_edges == len(cy_data.edges)


# ==========================================
# 4. Attack Path Discovery & Scoring
# ==========================================

def test_attack_path_discovery_and_scoring(db_session: Session):
    """Verify graph-based attack path discovery and prioritization scoring using NetworkX."""
    digital_twin = CyberRiskDigitalTwin(db_session)
    paths = digital_twin.discover_attack_paths(limit=20)

    assert len(paths) > 0, "Expected at least one attack path to be discovered"

    # Paths must be sorted by path_score descending
    scores = [p.path_score for p in paths]
    assert scores == sorted(scores, reverse=True)

    # Inspect top path
    top_path = paths[0]
    assert top_path.path_score > 0
    assert top_path.entry_point in ["Internet", "Internet Gateway", "PAYMENT-API-01", "AUTH-SERVICE-01", "WAF-PROD-01", "Bastion Host"]
    assert len(top_path.nodes) >= 2
    assert len(top_path.edges) == len(top_path.nodes) - 1
    assert top_path.hops == len(top_path.nodes) - 1

    # Check for PAYMENT-API-01 attack path to Customer Database
    payment_paths = [p for p in paths if any("PAYMENT-API-01" in a for a in p.critical_assets)]
    assert len(payment_paths) > 0
    p_path = payment_paths[0]
    assert p_path.path_score >= 85.0
    assert len(p_path.supporting_telemetry) > 0


# ==========================================
# 5. Asset Dependency Analysis
# ==========================================

def test_asset_dependency_analysis(db_session: Session):
    """Verify asset upstream/downstream and blast radius dependency analysis."""
    payment_api = db_session.scalar(select(Asset).where(Asset.name == "PAYMENT-API-01"))
    assert payment_api is not None

    digital_twin = CyberRiskDigitalTwin(db_session)
    deps = digital_twin.get_asset_dependencies(payment_api.id)

    assert deps is not None
    assert deps.asset_id == payment_api.id
    assert deps.asset_name == "PAYMENT-API-01"
    assert deps.internet_exposed is True
    assert len(deps.vulnerabilities) > 0
    assert len(deps.controls) > 0
    assert len(deps.business_services) > 0
    assert len(deps.connected_assets) > 0
    assert len(deps.attack_paths) > 0


# ==========================================
# 6. REST API Endpoints Verification
# ==========================================

def test_api_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_assets(client: TestClient):
    resp = client.get("/api/assets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 100


def test_api_graph(client: TestClient):
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert "summary" in data
    assert len(data["nodes"]) > 0
    assert len(data["edges"]) > 0


def test_api_attack_paths(client: TestClient):
    resp = client.get("/api/attack-paths?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for p in data:
        assert "path_id" in p
        assert "path_score" in p
        assert "entry_point" in p
        assert "target" in p
        assert "nodes" in p
        assert "edges" in p
        assert "critical_assets" in p


def test_api_asset_dependencies(client: TestClient):
    resp = client.get("/api/assets/2/dependencies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["asset_id"] == 2
    assert "upstream_dependencies" in data
    assert "downstream_dependencies" in data
    assert "connected_assets" in data
    assert "vulnerabilities" in data
    assert "controls" in data


def test_api_asset_attack_paths(client: TestClient):
    resp = client.get("/api/assets/2/attack-paths")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_api_correlation_payment_api_01(client: TestClient):
    resp = client.get("/api/correlation/asset/PAYMENT-API-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["asset_name"] == "PAYMENT-API-01"
    assert data["converged_risk_level"] == "critical"
    assert len(data["vulnerabilities"]) > 0
    assert len(data["siem_events"]) > 0
    assert len(data["edr_events"]) > 0
    assert len(data["cspm_findings"]) > 0
    assert len(data["risk_factors"]) >= 4


def test_api_p1_backward_compatibility(client: TestClient):
    """Verify that all original P1 endpoints continue to pass without error."""
    resp = client.get("/api/vulnerabilities")
    assert resp.status_code == 200

    resp = client.get("/api/threats")
    assert resp.status_code == 200

    resp = client.get("/api/controls")
    assert resp.status_code == 200

    resp = client.get("/api/risk/enterprise")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_expected_annual_loss" in data

    resp = client.get("/api/risk/assets")
    assert resp.status_code == 200

    resp = client.get("/api/compliance")
    assert resp.status_code == 200

    resp = client.post("/api/simulation/run", json={"budget": "1000000", "iterations": 500})
    assert resp.status_code == 200

    resp = client.post("/api/investments/optimize", json={"budget": "5000000"})
    assert resp.status_code == 200

    resp = client.post("/api/ingestion", json={
        "source": "asset_inventory",
        "records": [{"name": "TEST-NEW-ASSET-01", "asset_type": "application", "internet_exposed": False}]
    })
    assert resp.status_code == 200
    assert resp.json()["records_ingested"] == 1
