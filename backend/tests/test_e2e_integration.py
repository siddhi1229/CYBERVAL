import os
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import (
    Asset, BusinessService, Control, CveCatalogRecord,
    CspmFinding, EdrEvent, Investment, Risk, SecurityEvent, Threat, User, Vulnerability
)
from seed import seed


@pytest.fixture(scope="module")
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    seed(session)

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client(db_session):
    return TestClient(app)


def test_e2e_p1_to_p3_to_p5_pipeline(client, db_session):
    """Verifies complete end-to-end data pipeline from P1 to P3 to P5."""
    # 1. P1 Data Check
    asset = db_session.scalar(select(Asset).where(Asset.asset_id_code == "PAYMENT-API-01"))
    assert asset is not None
    assert asset.criticality == "CRITICAL"
    assert asset.internet_exposed is True

    # 2. P1 360 Correlation API
    resp_p1 = client.get("/api/correlation/asset/PAYMENT-API-01")
    assert resp_p1.status_code == 200
    p1_data = resp_p1.json()
    assert p1_data["asset"]["asset_id_code"] == "PAYMENT-API-01"
    assert p1_data["composite_risk_summary"]["is_high_risk_attack_target"] is True
    assert p1_data["composite_risk_summary"]["has_unmfa_privileged_access"] is True

    # 3. P3 Digital Twin Graph
    resp_graph = client.get("/api/graph")
    assert resp_graph.status_code == 200
    graph_data = resp_graph.json()
    assert len(graph_data["nodes"]) > 0
    assert len(graph_data["edges"]) > 0

    # 4. P3 Attack Paths Targeting PAYMENT-API-01 / Customer DB
    resp_paths = client.get("/api/attack-paths")
    assert resp_paths.status_code == 200
    paths = resp_paths.json()
    assert len(paths) > 0
    # Highest score path traverses Internet -> Gateway -> Payment API
    critical_paths = [p for p in paths if any("Payment API" in ca or "PAYMENT-API-01" in ca for ca in p["critical_assets"])]
    assert len(critical_paths) > 0

    # 5. P5 Mounted Investment Router Endpoints
    resp_controls = client.get("/api/investment/controls")
    assert resp_controls.status_code == 200
    controls_data = resp_controls.json()
    assert len(controls_data) > 0

    resp_opt = client.post("/api/investment/optimize", json={"total_budget": 5000000.0})
    assert resp_opt.status_code == 200
    opt_data = resp_opt.json()
    assert opt_data["total_investment"] <= 5000000.0
    assert opt_data["total_risk_reduction"] > 0
    assert len(opt_data["selected_controls"]) > 0

    resp_curves = client.get("/api/investment/curves")
    assert resp_curves.status_code == 200
    curves_data = resp_curves.json()
    assert len(curves_data["data_points"]) >= 2
    # Verify diminishing returns monotonicity
    efficiencies = [dp["marginal_efficiency"] for dp in curves_data["data_points"][1:]]
    for i in range(len(efficiencies) - 1):
        assert efficiencies[i] >= efficiencies[i+1], "Diminishing returns efficiency must decrease monotonically"

    resp_rosi = client.post("/api/investment/rosi?baseline_eal=48000000&effectiveness=0.75&annual_cost=1500000")
    assert resp_rosi.status_code == 200
    assert resp_rosi.json()["rosi_percentage"] == 2300.0


def test_all_18_api_endpoints_smoke(client):
    """Tests all 18 primary endpoints and records HTTP 200 OK statuses."""
    endpoints = [
        ("GET", "/health"),
        ("GET", "/api/assets"),
        ("GET", "/api/vulnerabilities"),
        ("GET", "/api/security-events"),
        ("GET", "/api/iam/users"),
        ("GET", "/api/iam/access"),
        ("GET", "/api/edr/events"),
        ("GET", "/api/cspm/findings"),
        ("GET", "/api/correlation/asset/PAYMENT-API-01"),
        ("GET", "/api/threats"),
        ("GET", "/api/controls"),
        ("GET", "/api/graph"),
        ("GET", "/api/attack-paths"),
        ("GET", "/api/risk/enterprise"),
        ("GET", "/api/risk/assets"),
        ("GET", "/api/compliance"),
        ("GET", "/api/investment/controls"),
        ("GET", "/api/investment/curves"),
    ]

    for method, ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Failed {ep}: got {resp.status_code}"
