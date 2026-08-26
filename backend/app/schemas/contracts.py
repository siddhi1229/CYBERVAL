from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AssetRead(APIModel):
    id: int
    asset_id_code: str | None = None
    name: str
    asset_type: str
    environment: str
    owner: str
    department: str | None = None
    criticality: str = "medium"
    business_value: Decimal = Decimal("0")
    internet_exposed: bool = False
    hostname: str | None = None
    ip_address: str | None = None
    cloud_provider: str | None = None
    status: str = "active"
    business_service_id: int | None = None


class UserRead(APIModel):
    id: int
    user_id_code: str | None = None
    email: str
    username: str | None = None
    display_name: str
    role: str
    department: str | None = None
    privilege_level: str = "standard"
    privileged: bool = False
    mfa_enabled: bool = True
    account_status: str = "active"
    failed_login_count: int = 0
    risky_login: bool = False
    last_login: datetime | None = None


class UserAssetAccessRead(APIModel):
    id: int
    user_id: int
    asset_id: int
    access_level: str
    status: str
    granted_at: datetime
    user_id_code: str | None = None
    username: str | None = None
    asset_id_code: str | None = None
    asset_name: str | None = None


class SecurityEventRead(APIModel):
    id: int
    event_id_code: str | None = None
    source: str
    event_type: str
    severity: str
    observed_at: datetime
    source_ip: str | None = None
    technique: str | None = None
    description: str | None = None
    user_id_code: str | None = None
    user_id: int | None = None
    asset_id: int | None = None
    asset_name: str | None = None


class EdrEventRead(APIModel):
    id: int
    event_id_code: str
    endpoint_id: str
    asset_id: int | None = None
    user_id_code: str | None = None
    user_id: int | None = None
    event_type: str
    process_name: str | None = None
    process_path: str | None = None
    indicator: str | None = None
    severity: str
    observed_at: datetime


class CspmFindingRead(APIModel):
    id: int
    finding_id_code: str
    provider: str
    resource_id: str
    resource_type: str
    finding_type: str
    description: str | None = None
    severity: str
    status: str
    internet_exposed: bool
    encrypted: bool
    remediation: str | None = None
    asset_id: int | None = None


class EnterpriseSyncRead(BaseModel):
    assets_count: int
    iam_users_count: int
    iam_access_count: int
    siem_events_count: int
    edr_events_count: int
    cspm_findings_count: int
    high_risk_scenario_confirmed: bool
    timestamp: datetime


class AssetCorrelationRead(BaseModel):
    asset: AssetRead
    vulnerabilities: list["VulnerabilityRead"]
    security_events: list[SecurityEventRead]
    edr_events: list[EdrEventRead]
    cspm_findings: list[CspmFindingRead]
    authorized_users: list[UserRead]
    composite_risk_summary: dict[str, object]


class VulnerabilityRead(APIModel):
    id: int
    cve_id: str
    title: str
    description: str | None = None
    cvss_score: Decimal
    severity: str
    status: str
    known_exploited: bool = False
    kev_date_added: datetime | None = None
    kev_due_date: datetime | None = None
    known_ransomware_use: bool = False
    affected_product: str | None = None
    cwe_id: str | None = None
    required_action: str | None = None
    sources: str = "NVD"
    composite_risk_priority: str = "UNKNOWN"
    asset_id: int
    asset_name: str | None = None
    internet_exposed: bool = False
    business_service_criticality: str | None = None


class CveCatalogRecordRead(APIModel):
    cve_id: str
    title: str
    description: str | None = None
    cvss_score: Decimal
    severity: str
    cvss_vector: str | None = None
    known_exploited: bool = False
    kev_date_added: datetime | None = None
    kev_due_date: datetime | None = None
    known_ransomware_campaign_use: bool = False
    affected_vendor: str | None = None
    affected_product: str | None = None
    cwe_ids: str | None = None
    required_action: str | None = None
    sources: str
    created_at: datetime
    updated_at: datetime


class CveCatalogSyncRequest(BaseModel):
    cve_ids: list[str] = Field(default_factory=list)
    sync_cisa_kev: bool = True
    sync_nvd: bool = True
    enrich_asset_vulnerabilities: bool = True


class CveCatalogSyncRead(BaseModel):
    cisa_kev_count: int
    nvd_count: int
    correlated_catalog_count: int
    asset_vulnerabilities_enriched: int
    timestamp: datetime


class AssetVulnerabilityAssociationRequest(BaseModel):
    cve_id: str = Field(min_length=5, max_length=40)
    asset_id: int = Field(gt=0)
    status: str = "open"
    custom_title: str | None = None


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
    source: str = Field(pattern="^(vulnerability_scanner|siem|iam|edr|cspm|asset_inventory|threat_intelligence|nvd|cisa_kev|cve_catalog)$")
    records: list[dict[str, object]] = Field(min_length=1)


class IngestionRead(BaseModel):
    source: str
    records_ingested: int
