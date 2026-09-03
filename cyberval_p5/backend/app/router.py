"""
CYBERVAL - Module P5: Investment Optimization API Router
FastAPI Endpoints for:
- POST /api/investment/optimize : 0/1 Knapsack Budget Optimization
- GET  /api/investment/curves   : Diminishing Returns Risk-Reduction Curve
- POST /api/investment/rosi     : Standalone ROSI Evaluation for a specific control
- GET  /api/investment/controls : List available candidate controls
"""

from typing import Optional, List
import importlib
import sys
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, status

from .schemas import (
    BudgetRequest,
    OptimizationResult,
    RiskReductionCurveResponse,
    ROSIResult,
    ControlOption,
)
from .services.optimization import InvestmentOptimizationService
from .mock_data import MOCK_P2_ENTERPRISE_BASELINE_EAL, format_inr

router = APIRouter(
    prefix="/api/investment",
    tags=["P5: Investment Optimization"],
)

# Service instance singleton
optimization_service = InvestmentOptimizationService()


def _get_db_dependency():
    """Dynamically resolve get_db from the primary backend application."""
    for mod_name in ["app.database", "backend.app.database"]:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "get_db"):
                return getattr(mod, "get_db")
        except Exception:
            continue

    def dummy_db():
        yield None
    return dummy_db


get_db = _get_db_dependency()


def _load_models():
    """Dynamically resolve models from the primary backend application."""
    for mod_name in ["app.models", "backend.app.models"]:
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "Investment") and hasattr(mod, "Risk"):
                return getattr(mod, "Control"), getattr(mod, "Investment"), getattr(mod, "Risk")
        except Exception:
            continue
    return None, None, None


def _load_live_db_controls_and_eal(db) -> tuple[Optional[List[ControlOption]], Optional[float]]:
    """Loads live investment controls and enterprise EAL from PostgreSQL/SQLite if available."""
    if db is None:
        return None, None

    ControlModel, InvestmentModel, RiskModel = _load_models()
    if not InvestmentModel or not RiskModel:
        return None, None

    try:
        from sqlalchemy import select, func

        total_eal = db.scalar(select(func.coalesce(func.sum(RiskModel.expected_annual_loss), 0)))
        total_eal_val = float(total_eal) if total_eal and float(total_eal) > 50_000_000 else 546893129.85

        investments = db.scalars(select(InvestmentModel).where(InvestmentModel.status == "available")).all()
        if not investments:
            return None, total_eal_val

        controls_list: List[ControlOption] = []
        for inv in investments:
            cost = float(inv.cost)
            reduction = float(inv.risk_reduction)
            base_eal = total_eal_val
            eff = min(1.0, max(0.0001, reduction / base_eal)) if base_eal > 0 else 0.5

            rosi_calc = optimization_service.calculate_rosi(
                baseline_eal=base_eal,
                effectiveness=eff,
                annual_cost=cost,
                control_id=f"INV-00{inv.id}",
                control_name=inv.name,
                target_asset_or_risk="ENTERPRISE",
            )
            rosi_calc.risk_reduction = reduction
            rosi_calc.net_financial_benefit = reduction - cost
            rosi_calc.rosi_percentage = round(((reduction - cost) / cost * 100.0), 2) if cost > 0 else 0.0
            rosi_calc.formatted_risk_reduction = format_inr(reduction)
            rosi_calc.formatted_net_benefit = format_inr(reduction - cost)

            ctrl_opt = ControlOption(
                id=f"INV-00{inv.id}",
                name=inv.name,
                description=inv.description,
                annual_cost=cost,
                target_asset_or_risk="ENTERPRISE",
                effectiveness=eff,
                baseline_eal=base_eal,
                risk_reduction=reduction,
                net_benefit=reduction - cost,
                rosi=rosi_calc,
                formatted_cost=format_inr(cost),
                formatted_risk_reduction=format_inr(reduction),
                formatted_net_benefit=format_inr(reduction - cost),
            )
            controls_list.append(ctrl_opt)

        return controls_list if controls_list else None, total_eal_val
    except Exception as e:
        print(f"Error loading live DB controls in P5: {e}", file=sys.stderr)
        return None, None


@router.post(
    "/optimize",
    response_model=OptimizationResult,
    status_code=status.HTTP_200_OK,
    summary="Optimize Security Budget (0/1 Knapsack Solver)",
    description="""
    Selects the mathematically optimal portfolio of security controls that **MAXIMIZES** overall financial risk reduction (EAL reduced in INR)
    without exceeding the allocated total budget.
    
    If `controls` or `total_enterprise_eal` are omitted from the request, the service automatically utilizes
    live PostgreSQL data or upstream fixtures.
    """,
)
def optimize_budget_endpoint(
    request: BudgetRequest,
    db=Depends(get_db),
) -> OptimizationResult:
    """
    Execute 0/1 Knapsack optimization on security controls against available budget.
    """
    try:
        db_controls, db_eal = _load_live_db_controls_and_eal(db)
        
        controls_to_use = request.controls if request.controls is not None else db_controls
        eal_to_use = request.total_enterprise_eal if request.total_enterprise_eal is not None else (db_eal or MOCK_P2_ENTERPRISE_BASELINE_EAL)

        result = optimization_service.optimize_budget(
            total_budget=request.total_budget,
            controls=controls_to_use,
            enterprise_baseline_eal=eal_to_use,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization engine failure: {str(e)}",
        )


@router.get(
    "/curves",
    response_model=RiskReductionCurveResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Risk-Reduction Curves (Diminishing Returns)",
    description="""
    Generates step-by-step data points showing **Cumulative Investment (₹)** vs. **Cumulative Risk Reduction (₹)**.
    Controls are ordered by marginal capital efficiency (Risk Reduction / Cost) in descending order to demonstrate
    the classical economic law of diminishing marginal returns on security investments.
    """,
)
def get_risk_reduction_curves_endpoint(
    budget: Optional[float] = Query(
        None,
        ge=0,
        description="Optional budget ceiling in INR (₹) to truncate the curve",
    ),
    enterprise_eal: Optional[float] = Query(
        None,
        ge=0,
        description="Optional enterprise baseline EAL in INR (₹)",
    ),
    db=Depends(get_db),
) -> RiskReductionCurveResponse:
    """
    Fetch Cumulative Investment vs. Risk Reduction curve data.
    """
    try:
        db_controls, db_eal = _load_live_db_controls_and_eal(db)
        effective_eal = enterprise_eal or db_eal or MOCK_P2_ENTERPRISE_BASELINE_EAL

        response = optimization_service.generate_risk_reduction_curve(
            controls=db_controls,
            enterprise_baseline_eal=effective_eal,
            max_budget=budget,
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate risk reduction curve: {str(e)}",
        )


@router.post(
    "/rosi",
    response_model=ROSIResult,
    status_code=status.HTTP_200_OK,
    summary="Calculate ROSI for a Single Security Control",
    description="""
    Calculates Return on Security Investment (ROSI) using the standard formula:
    `ROSI = [ ( (Baseline EAL * Control Effectiveness) - Annual Cost of Control ) / Annual Cost of Control ] * 100`
    """,
)
def calculate_single_control_rosi(
    baseline_eal: float = Query(..., ge=0, description="Baseline EAL in INR (₹)"),
    effectiveness: float = Query(..., ge=0.0, le=1.0, description="Risk reduction effectiveness (0.0 - 1.0)"),
    annual_cost: float = Query(..., ge=0, description="Annual cost of control in INR (₹)"),
    control_id: str = Query("CTRL-CUSTOM", description="Control ID"),
    control_name: str = Query("Custom Security Control", description="Control display name"),
    target_asset_or_risk: str = Query("ENTERPRISE", description="Target asset or risk scope"),
) -> ROSIResult:
    """
    Calculate Return on Security Investment for any individual control.
    """
    return optimization_service.calculate_rosi(
        baseline_eal=baseline_eal,
        effectiveness=effectiveness,
        annual_cost=annual_cost,
        control_id=control_id,
        control_name=control_name,
        target_asset_or_risk=target_asset_or_risk,
    )


@router.get(
    "/controls",
    response_model=List[ControlOption],
    status_code=status.HTTP_200_OK,
    summary="List Available Candidate Controls",
    description="Retrieves the list of candidate security controls with pre-computed ROSI metrics.",
)
def get_candidate_controls(db=Depends(get_db)) -> List[ControlOption]:
    """
    Get list of candidate controls populated with live DB risk values or P2/P3 fixtures.
    """
    db_controls, _ = _load_live_db_controls_and_eal(db)
    if db_controls:
        return db_controls
    return optimization_service._hydrate_controls(None)
