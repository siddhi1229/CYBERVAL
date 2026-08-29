"""
CYBERVAL - Module P5: Investment Optimization API Router
FastAPI Endpoints for:
- POST /api/investment/optimize : 0/1 Knapsack Budget Optimization
- GET  /api/investment/curves   : Diminishing Returns Risk-Reduction Curve
- POST /api/investment/rosi     : Standalone ROSI Evaluation for a specific control
- GET  /api/investment/controls : List available upstream mock controls
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, status

from .schemas import (
    BudgetRequest,
    OptimizationResult,
    RiskReductionCurveResponse,
    ROSIResult,
    ControlOption,
)
from .services.optimization import InvestmentOptimizationService
from .mock_data import MOCK_P2_ENTERPRISE_BASELINE_EAL

router = APIRouter(
    prefix="/api/investment",
    tags=["P5: Investment Optimization"],
)

# Service instance singleton
optimization_service = InvestmentOptimizationService()


@router.post(
    "/optimize",
    response_model=OptimizationResult,
    status_code=status.HTTP_200_OK,
    summary="Optimize Security Budget (0/1 Knapsack Solver)",
    description="""
    Selects the mathematically optimal portfolio of security controls that **MAXIMIZES** overall financial risk reduction (EAL reduced in INR)
    without exceeding the allocated total budget.
    
    If `controls` or `total_enterprise_eal` are omitted from the request, the service automatically utilizes
    upstream mock fixtures from P2 (Risk Engine) and P3 (Digital Twin Graph).
    """,
)
def optimize_budget_endpoint(request: BudgetRequest) -> OptimizationResult:
    """
    Execute 0/1 Knapsack optimization on security controls against available budget.
    """
    try:
        result = optimization_service.optimize_budget(
            total_budget=request.total_budget,
            controls=request.controls,
            enterprise_baseline_eal=request.total_enterprise_eal,
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
) -> RiskReductionCurveResponse:
    """
    Fetch Cumulative Investment vs. Risk Reduction curve data.
    """
    try:
        response = optimization_service.generate_risk_reduction_curve(
            controls=None,  # Uses mock controls if not specified
            enterprise_baseline_eal=enterprise_eal or MOCK_P2_ENTERPRISE_BASELINE_EAL,
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
    summary="List Available Upstream Candidate Controls",
    description="Retrieves the list of candidate security controls with pre-computed ROSI metrics.",
)
def get_candidate_controls() -> List[ControlOption]:
    """
    Get list of candidate controls populated with P2/P3 mock risk values and ROSI figures.
    """
    return optimization_service._hydrate_controls(None)
