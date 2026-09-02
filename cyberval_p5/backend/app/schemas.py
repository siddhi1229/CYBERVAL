"""
CYBERVAL - Module P5: Investment Optimization
Pydantic Schemas for Request/Response Payloads and Domain Models
All monetary values default to Indian Rupees (INR - ₹).
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ROSIResult(BaseModel):
    """
    Return on Security Investment (ROSI) calculation output model.
    Formula: ROSI = [ ( (Baseline EAL * Control Effectiveness) - Annual Cost ) / Annual Cost ] * 100
    """
    control_id: str = Field(..., description="Unique identifier of the evaluated security control")
    control_name: str = Field(..., description="Human-readable name of the security control")
    target_asset_or_risk: str = Field(..., description="Target asset or risk scope (from P2/P3)")
    baseline_eal: float = Field(..., ge=0, description="Baseline Expected Annual Loss in INR (₹)")
    control_effectiveness: float = Field(..., ge=0.0, le=1.0, description="Risk reduction effectiveness factor (0.0 to 1.0)")
    annual_cost: float = Field(..., ge=0, description="Annual implementation and operational cost in INR (₹)")
    risk_reduction: float = Field(..., ge=0, description="Financial risk reduced (Baseline EAL * Effectiveness) in INR (₹)")
    net_financial_benefit: float = Field(..., description="Net financial benefit (Risk Reduction - Annual Cost) in INR (₹)")
    rosi_percentage: float = Field(..., description="ROSI percentage (%)")
    currency: str = Field(default="INR", description="Currency code (Default: INR - ₹)")
    formatted_risk_reduction: Optional[str] = Field(None, description="Human-readable INR formatted risk reduction")
    formatted_annual_cost: Optional[str] = Field(None, description="Human-readable INR formatted annual cost")
    formatted_net_benefit: Optional[str] = Field(None, description="Human-readable INR formatted net benefit")

    model_config = {
        "json_schema_extra": {
            "example": {
                "control_id": "CTRL-MFA-001",
                "control_name": "Implement Privileged Identity MFA",
                "target_asset_or_risk": "PAYMENT-API-01",
                "baseline_eal": 42000000.0,
                "control_effectiveness": 0.75,
                "annual_cost": 1500000.0,
                "risk_reduction": 31500000.0,
                "net_financial_benefit": 30000000.0,
                "rosi_percentage": 2000.0,
                "currency": "INR",
                "formatted_risk_reduction": "₹3,15,00,000.00 (₹3.15 Cr)",
                "formatted_annual_cost": "₹15,00,000.00 (₹15.00 Lakh)",
                "formatted_net_benefit": "₹3,00,00,000.00 (₹3.00 Cr)"
            }
        }
    }


class ControlOption(BaseModel):
    """
    Representation of a candidate security control available for investment optimization.
    """
    id: str = Field(..., description="Unique control identifier (e.g., CTRL-MFA-001)")
    name: str = Field(..., description="Display name of the security control")
    description: Optional[str] = Field(None, description="Detailed description of the security control")
    annual_cost: float = Field(..., ge=0, description="Annual cost of implementing and operating the control in INR (₹)")
    target_asset_or_risk: str = Field(..., description="Targeted asset or risk exposure (from P2/P3)")
    effectiveness: float = Field(..., ge=0.0, le=1.0, description="Risk reduction fraction (0.0 to 1.0, e.g. 0.75 for 75%)")
    baseline_eal: Optional[float] = Field(None, ge=0, description="Baseline EAL of targeted asset in INR (₹). Auto-populated from P2/P3 mock if omitted.")
    risk_reduction: Optional[float] = Field(None, ge=0, description="Calculated risk reduction in INR (₹) = baseline_eal * effectiveness")
    rosi: Optional[ROSIResult] = Field(None, description="Pre-computed or populated ROSI analysis result")
    currency: str = Field(default="INR", description="Currency code (Default: INR - ₹)")

    @field_validator("effectiveness")
    @classmethod
    def validate_effectiveness(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Control effectiveness must be between 0.0 (0%) and 1.0 (100%).")
        return v


class BudgetRequest(BaseModel):
    """
    Payload for 0/1 Knapsack Budget Optimization request.
    """
    total_budget: float = Field(
        default=10_000_000.0,
        ge=0,
        description="Available capital budget in INR (₹). Default is ₹1,00,00,000 (₹1.00 Crore)."
    )
    controls: Optional[List[ControlOption]] = Field(
        default=None,
        description="List of candidate security controls. If empty or omitted, upstream P1/P2 mock controls are used."
    )
    total_enterprise_eal: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total enterprise baseline EAL in INR (₹). If omitted, upstream P2 mock baseline (₹10 Cr) is used."
    )
    currency: str = Field(default="INR", description="Currency code (Default: INR - ₹)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_budget": 10000000.0,
                "total_enterprise_eal": 100000000.0,
                "currency": "INR"
            }
        }
    }


class OptimizationResult(BaseModel):
    """
    Output model of the 0/1 Knapsack Optimization Engine.
    Represents the optimal portfolio of controls maximizing financial risk reduction within budget.
    """
    total_budget: float = Field(..., ge=0, description="Allocated budget limit in INR (₹)")
    total_investment: float = Field(..., ge=0, description="Total capital committed to selected controls in INR (₹)")
    remaining_budget: float = Field(..., ge=0, description="Unallocated / surplus budget in INR (₹)")
    budget_utilization_pct: float = Field(..., ge=0, le=100, description="Percentage of available budget utilized")
    
    baseline_enterprise_eal: float = Field(..., ge=0, description="Initial total enterprise baseline EAL in INR (₹)")
    total_risk_reduction: float = Field(..., ge=0, description="Maximized total risk reduction (EAL reduced) in INR (₹)")
    residual_enterprise_eal: float = Field(..., ge=0, description="Residual Enterprise EAL after applying selected controls in INR (₹)")
    overall_risk_reduction_pct: float = Field(..., ge=0, le=100, description="Percentage of total enterprise risk mitigated")
    
    portfolio_net_benefit: float = Field(..., description="Net financial benefit (Total Risk Reduction - Total Investment) in INR (₹)")
    portfolio_rosi_percentage: float = Field(..., description="Aggregate portfolio Return on Security Investment (%)")
    benefit_cost_ratio: float = Field(..., description="Benefit-to-Cost Ratio (Total Risk Reduction / Total Investment)")
    
    selected_controls: List[ControlOption] = Field(default_factory=list, description="Optimal set of selected security controls")
    unselected_controls: List[ControlOption] = Field(default_factory=list, description="Controls excluded due to budget constraints or lower efficiency")
    
    currency: str = Field(default="INR", description="Currency code (Default: INR - ₹)")
    
    # Formatted Indian Rupee string representations
    formatted_total_budget: Optional[str] = None
    formatted_total_investment: Optional[str] = None
    formatted_remaining_budget: Optional[str] = None
    formatted_baseline_eal: Optional[str] = None
    formatted_total_risk_reduction: Optional[str] = None
    formatted_residual_eal: Optional[str] = None
    formatted_net_benefit: Optional[str] = None


class CurveDataPoint(BaseModel):
    """
    A single coordinate point on the Cumulative Investment vs. Cumulative Risk Reduction curve.
    """
    step: int = Field(..., description="Step index (0 is baseline before any investment)")
    control_id: Optional[str] = Field(None, description="ID of control activated at this step")
    control_name: Optional[str] = Field(None, description="Name of control activated at this step")
    cumulative_investment: float = Field(..., ge=0, description="Cumulative capital invested in INR (₹)")
    cumulative_risk_reduction: float = Field(..., ge=0, description="Cumulative financial risk mitigated in INR (₹)")
    marginal_cost: float = Field(..., ge=0, description="Cost of this specific control in INR (₹)")
    marginal_risk_reduction: float = Field(..., ge=0, description="Risk reduction added by this control in INR (₹)")
    marginal_efficiency: float = Field(..., description="Marginal efficiency ratio (Marginal Risk Reduction / Marginal Cost)")
    marginal_rosi_pct: float = Field(..., description="Marginal ROSI (%) of the individual control")
    residual_eal: float = Field(..., ge=0, description="Residual Enterprise EAL after this step in INR (₹)")
    
    formatted_cumulative_investment: Optional[str] = None
    formatted_cumulative_risk_reduction: Optional[str] = None
    formatted_residual_eal: Optional[str] = None


class RiskReductionCurveResponse(BaseModel):
    """
    Response model containing data points for the Diminishing Returns Risk Reduction Curve.
    """
    baseline_enterprise_eal: float = Field(..., description="Enterprise baseline EAL in INR (₹)")
    total_available_controls: int = Field(..., description="Total candidate controls evaluated")
    currency: str = Field(default="INR", description="Currency code")
    data_points: List[CurveDataPoint] = Field(default_factory=list, description="Ordered curve points demonstrating diminishing returns")
    summary: str = Field(..., description="Executive narrative summary of the investment efficiency trajectory")
    formatted_baseline_enterprise_eal: Optional[str] = None
