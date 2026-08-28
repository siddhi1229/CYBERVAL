"""
P2 Quantitative Cyber Risk Engine Data Models.
Upstream contract for likelihood, financial impact, EAL, P95/P99, VaR,
risk drivers, control effectiveness, and scenario risk calculations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class FinancialImpactBreakdown:
    business_interruption: float  # In USD
    data_breach_and_forensics: float
    regulatory_fines_and_legal: float
    ransomware_extortion_risk: float
    reputation_and_customer_churn: float
    total_single_loss_expectancy: float  # Primary + Secondary loss


@dataclass
class ControlEffectiveness:
    control_id: str
    name: str
    category: str  # e.g., "Identity & Access", "Endpoint Defense", "Network Segmentation", "Vulnerability Mgmt"
    effectiveness_score: float  # 0.0 to 1.0 (1.0 = fully effective)
    target_asset_ids: List[str]
    description: str
    is_failing: bool
    status: str = "DEGRADED"


@dataclass
class RiskDriver:
    driver_id: str
    name: str
    category: str  # "VULNERABILITY", "IAM_MISCONFIG", "CLOUD_CONFIG", "ACTIVE_EXPLOIT"
    contribution_to_eal: float  # In USD
    percentage_contribution: float  # e.g., 42.5%
    description: str
    associated_asset_id: str
    associated_cve: Optional[str] = None


@dataclass
class AssetRiskProfile:
    asset_id: str
    asset_name: str
    annual_loss_event_frequency: float  # Events per year (e.g., 0.45)
    financial_impact: FinancialImpactBreakdown
    expected_annual_loss: float  # EAL in USD (e.g., $1,850,000)
    var_95: float  # 95% Value at Risk (1-year horizon)
    var_99: float  # 99% Value at Risk (P99 extreme tail loss)
    risk_rank: int
    risk_drivers: List[RiskDriver] = field(default_factory=list)


@dataclass
class EnterpriseRiskSummary:
    total_expected_annual_loss: float  # Enterprise total EAL
    enterprise_var_95: float
    enterprise_var_99: float
    overall_loss_event_frequency: float
    asset_profiles: Dict[str, AssetRiskProfile]
    weakest_controls: List[ControlEffectiveness]
    top_risk_drivers: List[RiskDriver]
    currency: str = "USD"
    calculation_timestamp: str = "2026-08-28T20:00:00Z"
    model_version: str = "P2-FAIR-MC-v3.4"


@dataclass
class ScenarioCalculationResult:
    scenario_name: str
    before_eal: float
    after_eal: float
    risk_reduction_amount: float
    percentage_reduction: float
    before_var_95: float
    after_var_95: float
    affected_assets: List[str]
    affected_controls: List[str]
    assumptions_applied: List[str]
    calculation_details: Dict[str, Any] = field(default_factory=dict)
