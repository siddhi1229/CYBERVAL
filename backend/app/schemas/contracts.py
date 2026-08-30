from datetime import datetime
from decimal import Decimal
from typing import Any

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


# ==========================================
# Cytoscape Graph Schemas (P3 / P6 Frontend)
# ==========================================

class CytoscapeNodeData(BaseModel):
    id: str
    label: str
    type: str  # Asset, Vulnerability, User, Threat, Control, BusinessService, SecurityEvent, EDREvent, CSPMFinding
    category: str | None = None
    db_id: int | None = None
    risk_score: float | None = None
    internet_exposed: bool | None = None
    environment: str | None = None
    owner: str | None = None
    criticality: str | None = None
    cvss_score: float | None = None
    severity: str | None = None
    cve_id: str | None = None
    role: str | None = None
    privileged: bool | None = None
    effectiveness: float | None = None
    annual_revenue: float | None = None
    annual_frequency: float | None = None
    source: str | None = None
    event_type: str | None = None
    mitre_technique: str | None = None
    observed_at: str | None = None
    details: dict[str, Any] | None = None


class CytoscapeNode(BaseModel):
    data: CytoscapeNodeData


class CytoscapeEdgeData(BaseModel):
    id: str
    source: str
    target: str
    relationship: str  # HAS_ACCESS, HAS_VULNERABILITY, PROTECTED_BY, PART_OF, CONNECTS_TO, TARGETS, OBSERVED_ON, AFFECTS, DEPENDS_ON, EXPLOITS
    label: str | None = None
    weight: float | None = 1.0
    is_synthetic: bool = False
    details: dict[str, Any] | None = None


class CytoscapeEdge(BaseModel):
    data: CytoscapeEdgeData


class CytoscapeGraphSummary(BaseModel):
    total_nodes: int
    total_edges: int
    node_types: dict[str, int]
    edge_types: dict[str, int]


class CytoscapeGraphResponse(BaseModel):
    nodes: list[CytoscapeNode]
    edges: list[CytoscapeEdge]
    summary: CytoscapeGraphSummary | None = None


# ==========================================
# Attack Path Schemas (P3)
# ==========================================

class SupportingTelemetryRead(BaseModel):
    source: str  # siem, edr, cspm, iam
    event_type: str
    severity: str
    asset_id: int | None = None
    asset_name: str | None = None
    mitre_technique: str | None = None
    observed_at: str | None = None
    details: dict[str, Any] | None = None


class AttackPathEdgeRead(BaseModel):
    source: str
    target: str
    relationship: str


class AttackPathRead(BaseModel):
    path_id: str
    nodes: list[str]
    entry_point: str = "Internet"
    target: str = "Critical Asset"
    path_score: float = 0.0
    hops: int = 1
    edges: list[AttackPathEdgeRead] = Field(default_factory=list)
    critical_assets: list[str] = Field(default_factory=list)
    critical_vulnerabilities: list[str] = Field(default_factory=list)
    control_weaknesses: list[str] = Field(default_factory=list)
    supporting_telemetry: list[SupportingTelemetryRead] = Field(default_factory=list)
    vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    controls: list[dict[str, Any]] = Field(default_factory=list)
    users: list[dict[str, Any]] = Field(default_factory=list)
    business_services: list[str] = Field(default_factory=list)
    # P1/P2 compatibility fields:
    likelihood: Decimal = Decimal("0.1")
    expected_annual_loss: Decimal = Decimal("0.0")
    risk_score: float | None = None


# ==========================================
# Asset Dependency Schemas (P3)
# ==========================================

class AssetDependencyRead(BaseModel):
    asset_id: int
    asset_name: str
    asset_type: str
    environment: str
    owner: str
    internet_exposed: bool
    upstream_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    downstream_dependencies: list[dict[str, Any]] = Field(default_factory=list)
    connected_assets: list[dict[str, Any]] = Field(default_factory=list)
    users_with_access: list[dict[str, Any]] = Field(default_factory=list)
    vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    controls: list[dict[str, Any]] = Field(default_factory=list)
    business_services: list[dict[str, Any]] = Field(default_factory=list)
    attack_paths: list[dict[str, Any]] = Field(default_factory=list)


# ==========================================
# Multi-Source Asset Correlation Schemas (P3)
# ==========================================

class AssetCorrelationRead(BaseModel):
    asset_id: int
    asset_name: str
    asset_type: str
    internet_exposed: bool
    environment: str
    owner: str
    business_service: str | None = None
    business_service_criticality: str | None = None
    vulnerabilities: list[dict[str, Any]] = Field(default_factory=list)
    iam_access: list[dict[str, Any]] = Field(default_factory=list)
    siem_events: list[dict[str, Any]] = Field(default_factory=list)
    edr_events: list[dict[str, Any]] = Field(default_factory=list)
    cspm_findings: list[dict[str, Any]] = Field(default_factory=list)
    controls: list[dict[str, Any]] = Field(default_factory=list)
    threats: list[dict[str, Any]] = Field(default_factory=list)
    converged_risk_level: str = "medium"
    risk_factors: list[str] = Field(default_factory=list)
    graph_risk_score: float = 0.0


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
