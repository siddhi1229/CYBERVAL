from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AssetRead(APIModel):
    id: int
    name: str
    asset_type: str
    environment: str
    owner: str
    internet_exposed: bool
    business_service_id: int | None


class VulnerabilityRead(APIModel):
    id: int
    cve_id: str
    title: str
    cvss_score: Decimal
    severity: str
    status: str
    asset_id: int


class ThreatRead(APIModel):
    id: int
    name: str
    category: str
    annual_frequency: Decimal
    source: str


class ControlRead(APIModel):
    id: int
    name: str
    description: str
    effectiveness: Decimal
    status: str


class RiskRead(APIModel):
    id: int
    asset_id: int
    likelihood: Decimal
    financial_impact: Decimal
    expected_annual_loss: Decimal
    confidence: Decimal
    calculation_version: str


class EnterpriseRiskRead(BaseModel):
    total_expected_annual_loss: Decimal
    risk_count: int
    highest_risk_asset_id: int | None
    calculation_version: str


class AttackPathRead(BaseModel):
    path_id: str
    nodes: list[str]
    likelihood: Decimal
    expected_annual_loss: Decimal


class RecommendationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class RecommendationRead(BaseModel):
    answer: str
    source_risk_ids: list[int]
    generated_at: datetime


class SimulationRequest(BaseModel):
    budget: Decimal = Field(ge=0)
    iterations: int = Field(default=1000, ge=100, le=100000)


class SimulationRead(BaseModel):
    iterations: int
    mean_loss: Decimal
    median_loss: Decimal
    p90_loss: Decimal
    p95_loss: Decimal
    p99_loss: Decimal


class OptimizationRequest(BaseModel):
    budget: Decimal = Field(ge=0)


class OptimizationRead(BaseModel):
    budget: Decimal
    selected_investment_ids: list[int]
    projected_risk_reduction: Decimal
    remaining_budget: Decimal


class ComplianceRead(BaseModel):
    framework: str
    mapped_controls: int
    total_controls: int


class IngestionRequest(BaseModel):
    source: str = Field(pattern="^(vulnerability_scanner|siem|iam|edr|cspm|asset_inventory|threat_intelligence)$")
    records: list[dict[str, object]] = Field(min_length=1)


class IngestionRead(BaseModel):
    source: str
    records_ingested: int
