from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset, Control, FrameworkControl, Investment, Risk, Threat, Vulnerability
from app.services.ingestion import NormalizedIngestionService
from app.schemas.contracts import (
    AssetRead, AttackPathRead, ComplianceRead, ControlRead, EnterpriseRiskRead,
    OptimizationRead, OptimizationRequest, RecommendationRead, RecommendationRequest,
    RiskRead, SimulationRead, SimulationRequest, ThreatRead, VulnerabilityRead,
    IngestionRead, IngestionRequest,
)

router = APIRouter(prefix="/api")
ingestion_service = NormalizedIngestionService()


@router.post("/ingestion", response_model=IngestionRead, summary="Normalize telemetry into shared entities")
def ingest_telemetry(request: IngestionRequest, db: Session = Depends(get_db)):
    count = ingestion_service.ingest(db, request.source, request.records)
    return IngestionRead(source=request.source, records_ingested=count)


@router.get("/assets", response_model=list[AssetRead], summary="List normalized assets")
def list_assets(db: Session = Depends(get_db)):
    return db.scalars(select(Asset).order_by(Asset.id)).all()


@router.get("/vulnerabilities", response_model=list[VulnerabilityRead], summary="List asset vulnerabilities")
def list_vulnerabilities(db: Session = Depends(get_db)):
    return db.scalars(select(Vulnerability).order_by(Vulnerability.id)).all()


@router.get("/threats", response_model=list[ThreatRead], summary="List threat intelligence")
def list_threats(db: Session = Depends(get_db)):
    return db.scalars(select(Threat).order_by(Threat.id)).all()


@router.get("/controls", response_model=list[ControlRead], summary="List master security controls")
def list_controls(db: Session = Depends(get_db)):
    return db.scalars(select(Control).order_by(Control.id)).all()


@router.get("/risk/enterprise", response_model=EnterpriseRiskRead, summary="Get enterprise financial risk")
def enterprise_risk(db: Session = Depends(get_db)):
    total, count = db.execute(select(func.coalesce(func.sum(Risk.expected_annual_loss), 0), func.count(Risk.id))).one()
    highest = db.scalar(select(Risk.asset_id).order_by(Risk.expected_annual_loss.desc()).limit(1))
    return EnterpriseRiskRead(total_expected_annual_loss=total, risk_count=count, highest_risk_asset_id=highest, calculation_version="baseline-1")


@router.get("/risk/assets", response_model=list[RiskRead], summary="Get financial risk by asset")
def asset_risk(db: Session = Depends(get_db)):
    return db.scalars(select(Risk).order_by(Risk.expected_annual_loss.desc())).all()


@router.get("/attack-paths", response_model=list[AttackPathRead], summary="Get attack path contract")
def attack_paths(db: Session = Depends(get_db)):
    risks = db.scalars(select(Risk).order_by(Risk.expected_annual_loss.desc()).limit(20)).all()
    return [AttackPathRead(path_id=f"asset-risk-{risk.asset_id}", nodes=["Internet", f"Asset:{risk.asset_id}"], likelihood=risk.likelihood, expected_annual_loss=risk.expected_annual_loss) for risk in risks]


@router.post("/ai/recommend", response_model=RecommendationRead, summary="Request a risk-grounded recommendation")
def recommend(request: RecommendationRequest, db: Session = Depends(get_db)):
    risk = db.scalar(select(Risk).order_by(Risk.expected_annual_loss.desc()).limit(1))
    return RecommendationRead(answer="Risk-grounded recommendation requires the decision-support module.", source_risk_ids=[risk.id] if risk else [], generated_at=datetime.now(UTC))


@router.post("/ai/query", response_model=RecommendationRead, summary="Ask a risk-grounded question")
def query_ai(request: RecommendationRequest, db: Session = Depends(get_db)):
    return recommend(request, db)


@router.post("/simulation/run", response_model=SimulationRead, summary="Run a what-if simulation")
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    total = db.scalar(select(func.coalesce(func.sum(Risk.expected_annual_loss), 0))) or Decimal("0")
    return SimulationRead(iterations=request.iterations, mean_loss=total, median_loss=total, p90_loss=total, p95_loss=total, p99_loss=total)


@router.post("/investments/optimize", response_model=OptimizationRead, summary="Optimize investments under a budget")
def optimize(request: OptimizationRequest, db: Session = Depends(get_db)):
    investments = db.scalars(select(Investment).where(Investment.status == "available").order_by(Investment.risk_reduction.desc())).all()
    selected = []
    remaining = request.budget
    reduction = Decimal("0")
    for investment in investments:
        if investment.cost <= remaining:
            selected.append(investment.id)
            remaining -= investment.cost
            reduction += investment.risk_reduction
    return OptimizationRead(budget=request.budget, selected_investment_ids=selected, projected_risk_reduction=reduction, remaining_budget=remaining)


@router.get("/compliance", response_model=list[ComplianceRead], summary="Get framework control coverage")
def compliance(db: Session = Depends(get_db)):
    rows = db.execute(select(FrameworkControl.framework, func.count(FrameworkControl.id)).group_by(FrameworkControl.framework)).all()
    return [ComplianceRead(framework=framework, mapped_controls=count, total_controls=count) for framework, count in rows]
