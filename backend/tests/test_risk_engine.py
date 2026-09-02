"""P2 risk-engine tests.

All tests run on in-memory SQLite seeded with P1's deterministic dataset
(``seed()``), so they exercise the real P1 -> P2 path without PostgreSQL.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Asset, Risk, RiskHistory
from app.services.risk.config import get_default_config
from app.services.risk.engine import RiskEngine
from app.services.risk.impact import compute_financial_impact
from app.services.risk.likelihood import compute_likelihood
from app.services.risk.monte_carlo import simulate_asset_losses, summarize
from app.services.risk.signals import extract_asset_signals
from seed import seed

SEED_KW = dict(asset_count=45, user_count=20, siem_count=50, edr_count=30, cspm_count=20)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    seed(session, **SEED_KW)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override():
        yield db_session

    app.dependency_overrides[get_db] = override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def engine():
    cfg = get_default_config()
    cfg.monte_carlo.iterations = 15_000
    cfg.monte_carlo.list_iterations = 8_000
    return RiskEngine(cfg)


def _asset(db, code):
    return db.query(Asset).filter_by(asset_id_code=code).one()


def _portfolio(engine, db):
    return engine.calculate_portfolio(db, iterations=12_000, persist=False)


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------
def test_payment_api_signals_are_elevated(db_session, engine):
    asset = _asset(db_session, "PAYMENT-API-01")
    sig = extract_asset_signals(asset, engine.config, threat_baseline=0.4)
    f = sig.factors
    assert f["internet_exposure"] >= 0.8
    assert f["known_exploitation"] >= 0.8  # CVE-2021-44228 KEV + ransomware
    assert f["vulnerability_severity"] >= 0.9  # CVSS 10.0 xz / log4shell
    assert f["identity_risk"] >= 0.6  # USR-001 privileged, MFA off, 17 failed logins
    assert f["endpoint_risk"] >= 0.6  # credential_dumping EDR indicator
    assert f["cloud_posture_risk"] >= 0.4  # OPEN_SECURITY_GROUP
    assert sig.active_attack is True
    assert sig.evidence["privileged_users_without_mfa"] >= 1


def test_internal_asset_without_vulns_has_low_signals(db_session, engine):
    candidates = [
        a
        for a in db_session.query(Asset).all()
        if not a.internet_exposed and not a.vulnerabilities and not a.cspm_findings
    ]
    assert candidates
    sig = extract_asset_signals(candidates[0], engine.config, threat_baseline=0.4)
    assert sig.factors["known_exploitation"] == 0.0
    assert sig.factors["internet_exposure"] == 0.0
    assert sig.factors["cloud_posture_risk"] == 0.0


# ---------------------------------------------------------------------------
# Likelihood
# ---------------------------------------------------------------------------
def test_likelihood_score_is_not_a_probability(engine):
    high = {k: 1.0 for k in engine.config.likelihood.factor_weights}
    res = compute_likelihood(high, engine.config)
    assert res.likelihood_score == pytest.approx(1.0, abs=1e-6)
    assert res.annual_incident_probability <= engine.config.likelihood.annual_probability_cap
    assert res.annual_incident_probability != res.likelihood_score


def test_likelihood_monotonic_in_factors(engine):
    low = {k: 0.1 for k in engine.config.likelihood.factor_weights}
    mid = {k: 0.5 for k in engine.config.likelihood.factor_weights}
    hi = {k: 0.9 for k in engine.config.likelihood.factor_weights}
    a = compute_likelihood(low, engine.config).annual_incident_probability
    b = compute_likelihood(mid, engine.config).annual_incident_probability
    c = compute_likelihood(hi, engine.config).annual_incident_probability
    assert a < b < c
    assert all(0.0 <= x <= 1.0 for x in (a, b, c))


# ---------------------------------------------------------------------------
# Financial impact
# ---------------------------------------------------------------------------
def test_financial_impact_components_and_inr(db_session, engine):
    asset = _asset(db_session, "PAYMENT-API-01")
    sig = extract_asset_signals(asset, engine.config, threat_baseline=0.4)
    imp = compute_financial_impact(asset, sig, engine.config)
    comps = imp.components()
    assert set(comps) == {
        "downtime_cost",
        "data_breach_cost",
        "recovery_cost",
        "regulatory_cost",
        "business_loss",
        "reputational_loss",
    }
    assert imp.total == pytest.approx(sum(comps.values()))
    assert all(v >= 0 for v in comps.values())
    assert imp.total > 0


def test_impact_assumptions_are_configurable(db_session):
    asset = _asset(db_session, "PAYMENT-API-01")
    base_cfg = get_default_config()
    hi_cfg = base_cfg.merged_with({"impact": {"breach_cost_per_record_inr": 9_000.0}})
    sig = extract_asset_signals(asset, base_cfg, threat_baseline=0.4)
    base = compute_financial_impact(asset, sig, base_cfg)
    bumped = compute_financial_impact(asset, extract_asset_signals(asset, hi_cfg, threat_baseline=0.4), hi_cfg)
    assert bumped.data_breach_cost > base.data_breach_cost
    assert bumped.total > base.total


# ---------------------------------------------------------------------------
# EAL
# ---------------------------------------------------------------------------
def test_eal_equals_probability_times_impact(db_session, engine):
    asset = _asset(db_session, "PAYMENT-API-01")
    pf = engine.calculate_portfolio(db_session, asset_ids=[asset.id], iterations=10_000, persist=False)
    r = pf.assets[0]
    assert r.expected_annual_loss == pytest.approx(
        r.annual_incident_probability * r.financial_impact, rel=1e-3
    )


# ---------------------------------------------------------------------------
# Monte Carlo / VaR
# ---------------------------------------------------------------------------
def test_monte_carlo_percentiles_ordered_and_var_matches(engine):
    losses = simulate_asset_losses(0.4, 40_000_000.0, engine.config, seed_offset=2, iterations=40_000)
    mc = summarize(losses, engine.config)
    assert mc.p50 <= mc.p90 <= mc.p95 <= mc.p99
    assert mc.var95 == pytest.approx(mc.p95)
    assert mc.var99 == pytest.approx(mc.p99)
    assert mc.expected_shortfall_95 >= mc.p95
    # mean annual loss ~ prob * impact for a single-event-dominated model
    assert mc.mean == pytest.approx(0.4 * 40_000_000.0, rel=0.15)


def test_monte_carlo_is_deterministic_with_seed(engine):
    a = simulate_asset_losses(0.3, 25_000_000.0, engine.config, seed_offset=7, iterations=10_000)
    b = simulate_asset_losses(0.3, 25_000_000.0, engine.config, seed_offset=7, iterations=10_000)
    assert (a == b).all()


def test_zero_impact_yields_zero_losses(engine):
    losses = simulate_asset_losses(0.5, 0.0, engine.config, seed_offset=1, iterations=1_000)
    assert losses.sum() == 0.0


# ---------------------------------------------------------------------------
# Aggregation (no double counting)
# ---------------------------------------------------------------------------
def test_enterprise_eal_is_sum_of_asset_eal(db_session, engine):
    pf = _portfolio(engine, db_session)
    assert pf.enterprise.expected_annual_loss == pytest.approx(
        sum(a.expected_annual_loss for a in pf.assets), rel=1e-6
    )
    # Every business service is a strict subset of the enterprise.
    for g in pf.business_services:
        assert g.expected_annual_loss <= pf.enterprise.expected_annual_loss + 1.0
        assert set(g.asset_ids).issubset({a.asset_id for a in pf.assets})


def test_service_monte_carlo_not_greater_than_enterprise(db_session, engine):
    pf = _portfolio(engine, db_session)
    for g in pf.business_services:
        assert g.monte_carlo.p95 <= pf.enterprise.monte_carlo.p95 + 1.0


# ---------------------------------------------------------------------------
# Risk drivers
# ---------------------------------------------------------------------------
def test_risk_drivers_sum_to_one_and_rank_payment_api(db_session, engine):
    asset = _asset(db_session, "PAYMENT-API-01")
    pf = engine.calculate_portfolio(db_session, asset_ids=[asset.id], iterations=8_000, persist=False)
    drivers = pf.assets[0].risk_drivers
    assert drivers
    assert sum(d["contribution"] for d in drivers) == pytest.approx(1.0, abs=1e-3)
    top_factors = {d["factor"] for d in drivers[:4]}
    assert top_factors & {"known_exploited_vulnerability", "internet_exposure", "critical_vulnerability"}


# ---------------------------------------------------------------------------
# Control effectiveness / residual risk
# ---------------------------------------------------------------------------
def test_control_effectiveness_in_range_and_residual_leq_inherent(db_session, engine):
    pf = _portfolio(engine, db_session)
    for r in pf.assets:
        assert 0.0 <= r.control_effectiveness <= 1.0
        assert 0.0 <= r.control_weakness <= 1.0
        assert r.residual_expected_annual_loss <= r.inherent_expected_annual_loss + 1.0
        assert r.risk_reduction_from_controls >= 0.0


def test_weak_control_scenario_increases_risk(db_session):
    asset = _asset(db_session, "PAYMENT-API-01")
    strong = RiskEngine(get_default_config())
    weak = RiskEngine(
        get_default_config().merged_with(
            {"controls": {"status_inactive_factor": 0.0}}
        )
    )
    # Disable every control via a config that treats them as inactive.
    from app.models import Control

    for c in db_session.query(Control).all():
        c.status = "inactive"
    db_session.commit()

    s = strong.calculate_portfolio(db_session, asset_ids=[asset.id], iterations=8_000, persist=False).assets[0]
    w = weak.calculate_portfolio(db_session, asset_ids=[asset.id], iterations=8_000, persist=False).assets[0]
    assert w.control_effectiveness <= s.control_effectiveness
    assert w.expected_annual_loss >= s.expected_annual_loss


# ---------------------------------------------------------------------------
# PAYMENT-API-01 primary integration test
# ---------------------------------------------------------------------------
def test_payment_api_is_top_risk(db_session, engine):
    pf = _portfolio(engine, db_session)
    ranked = sorted(pf.assets, key=lambda a: a.risk_score, reverse=True)
    assert ranked[0].asset_code == "PAYMENT-API-01"

    pay = next(a for a in pf.assets if a.asset_code == "PAYMENT-API-01")
    low = min(pf.assets, key=lambda a: a.risk_score)
    assert pay.risk_score > 4 * low.risk_score
    assert pay.expected_annual_loss > 10 * low.expected_annual_loss
    assert pay.risk_score >= 80
    assert 0.0 < pay.annual_incident_probability <= 1.0
    assert pay.monte_carlo.p99 >= pay.monte_carlo.p95 >= pay.expected_annual_loss


def test_critical_business_service_dominates(db_session, engine):
    pf = _portfolio(engine, db_session)
    names = [g.label for g in pf.business_services]
    assert "Payment Service" in names


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def test_api_calculate_persists(client, db_session):
    resp = client.post("/api/risk/calculate", json={"iterations": 5_000, "persist": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["persisted"] is True
    assert body["assets"]
    pay = next(a for a in body["assets"] if a["asset_code"] == "PAYMENT-API-01")
    assert pay["risk_score"] >= 80
    assert pay["expected_annual_loss"] > 0
    assert pay["risk_drivers"]
    # persistence: P1 risks row upserted + risk_history appended
    assert db_session.query(Risk).count() >= len(body["assets"])
    assert db_session.query(RiskHistory).filter_by(scope="asset").count() >= len(body["assets"])
    assert db_session.query(RiskHistory).filter_by(scope="enterprise").count() == 1


def test_api_risk_assets_and_detail(client):
    lst = client.get("/api/risk/assets?limit=100")
    assert lst.status_code == 200
    rows = lst.json()
    assert rows == sorted(rows, key=lambda r: r["expected_annual_loss"], reverse=True)
    pay = next(r for r in rows if r["asset_code"] == "PAYMENT-API-01")

    detail = client.get(f"/api/risk/assets/{pay['asset_id']}")
    assert detail.status_code == 200
    d = detail.json()
    assert d["monte_carlo"]["p95"] <= d["monte_carlo"]["p99"]
    assert set(d["financial_impact_breakdown"]) >= {"downtime_cost", "data_breach_cost"}
    assert d["control_evaluations"]
    assert d["signals"]["factors"]["known_exploitation"] >= 0.8


def test_api_enterprise_and_drivers(client):
    ent = client.get("/api/risk/enterprise")
    assert ent.status_code == 200
    e = ent.json()
    assert e["total_expected_annual_loss"] == pytest.approx(
        e["enterprise"]["expected_annual_loss"], rel=1e-6
    )
    assert e["business_services"]
    assert e["enterprise"]["var95"] == pytest.approx(e["enterprise"]["monte_carlo"]["p95"])

    drv = client.get("/api/risk/drivers?scope=enterprise&top=5")
    assert drv.status_code == 200
    ds = drv.json()
    assert 1 <= len(ds) <= 5
    assert all("factor" in d and "contribution" in d for d in ds)


def test_api_trends_after_two_runs(client):
    client.post("/api/risk/calculate", json={"iterations": 4_000, "persist": True})
    client.post("/api/risk/calculate", json={"iterations": 4_000, "persist": True})
    tr = client.get("/api/risk/trends?scope=enterprise")
    assert tr.status_code == 200
    body = tr.json()
    assert len(body["points"]) >= 2
    assert "note" in body


def test_api_trends_requires_ref_for_asset_scope(client):
    resp = client.get("/api/risk/trends?scope=asset")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# P1 endpoints still work with P2 mounted
# ---------------------------------------------------------------------------
def test_p1_endpoints_unaffected(client):
    assert client.get("/api/assets").status_code == 200
    assert client.get("/health").status_code == 200
    corr = client.get("/api/correlation/asset/PAYMENT-API-01")
    assert corr.status_code == 200
    assert corr.json()["composite_risk_summary"]["is_high_risk_attack_target"] is True
