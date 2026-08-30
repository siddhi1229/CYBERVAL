from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BusinessService(TimestampMixin, Base):
    __tablename__ = "business_services"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    owner: Mapped[str] = mapped_column(String(160))
    criticality: Mapped[str] = mapped_column(String(30), default="medium")
    annual_revenue: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    assets: Mapped[list["Asset"]] = relationship(back_populates="business_service")


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id_code: Mapped[str | None] = mapped_column(String(60), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    asset_type: Mapped[str] = mapped_column(String(60))
    environment: Mapped[str] = mapped_column(String(40), default="production")
    owner: Mapped[str] = mapped_column(String(160))
    department: Mapped[str | None] = mapped_column(String(100), default="Engineering", nullable=True)
    criticality: Mapped[str] = mapped_column(String(30), default="medium")
    business_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    internet_exposed: Mapped[bool] = mapped_column(Boolean, default=False)
    hostname: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(60), nullable=True)
    cloud_provider: Mapped[str | None] = mapped_column(String(40), default="on-premise", nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    business_service_id: Mapped[int | None] = mapped_column(ForeignKey("business_services.id"))
    business_service: Mapped[BusinessService | None] = relationship(back_populates="assets")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    risks: Mapped[list["Risk"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    security_events: Mapped[list["SecurityEvent"]] = relationship(back_populates="asset")
    iam_accesses: Mapped[list["UserAssetAccess"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    edr_events: Mapped[list["EdrEvent"]] = relationship(back_populates="asset")
    cspm_findings: Mapped[list["CspmFinding"]] = relationship(back_populates="asset")


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id_code: Mapped[str | None] = mapped_column(String(60), unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String(240), unique=True)
    username: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(60))
    department: Mapped[str | None] = mapped_column(String(100), default="IT", nullable=True)
    privilege_level: Mapped[str] = mapped_column(String(30), default="standard")
    privileged: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    account_status: Mapped[str] = mapped_column(String(30), default="active")
    failed_login_count: Mapped[int] = mapped_column(default=0)
    risky_login: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    asset_accesses: Mapped[list["UserAssetAccess"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserAssetAccess(TimestampMixin, Base):
    __tablename__ = "iam_access"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    access_level: Mapped[str] = mapped_column(String(40), default="read")
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(30), default="active")
    user: Mapped[User] = relationship(back_populates="asset_accesses")
    asset: Mapped[Asset] = relationship(back_populates="iam_accesses")


class SecurityEvent(TimestampMixin, Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id_code: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(60))
    event_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_ip: Mapped[str | None] = mapped_column(String(60), nullable=True)
    technique: Mapped[str | None] = mapped_column(String(60), nullable=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    user_id_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    asset: Mapped[Asset | None] = relationship(back_populates="security_events")


class EdrEvent(TimestampMixin, Base):
    __tablename__ = "edr_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id_code: Mapped[str] = mapped_column(String(60), index=True)
    endpoint_id: Mapped[str] = mapped_column(String(60), index=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    user_id_code: Mapped[str | None] = mapped_column(String(60), nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100))
    process_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    process_path: Mapped[str | None] = mapped_column(String(260), nullable=True)
    indicator: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    asset: Mapped[Asset | None] = relationship(back_populates="edr_events")


class CspmFinding(TimestampMixin, Base):
    __tablename__ = "cspm_findings"
    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id_code: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="AWS")
    resource_id: Mapped[str] = mapped_column(String(160), index=True)
    resource_type: Mapped[str] = mapped_column(String(60))
    finding_type: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="high")
    status: Mapped[str] = mapped_column(String(30), default="open")
    internet_exposed: Mapped[bool] = mapped_column(Boolean, default=False)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True)
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    asset: Mapped[Asset | None] = relationship(back_populates="cspm_findings")


class CveCatalogRecord(TimestampMixin, Base):
    __tablename__ = "cve_catalog"
    cve_id: Mapped[str] = mapped_column(String(40), primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cvss_score: Mapped[Decimal] = mapped_column(Numeric(4, 1), default=0)
    severity: Mapped[str] = mapped_column(String(20), default="UNKNOWN")
    cvss_vector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    known_exploited: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    kev_date_added: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kev_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    known_ransomware_campaign_use: Mapped[bool] = mapped_column(Boolean, default=False)
    affected_vendor: Mapped[str | None] = mapped_column(String(160), nullable=True)
    affected_product: Mapped[str | None] = mapped_column(String(240), nullable=True)
    cwe_ids: Mapped[str | None] = mapped_column(String(120), nullable=True)
    required_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[str] = mapped_column(String(100), default="NVD")
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True, default="{}")


class Vulnerability(TimestampMixin, Base):
    __tablename__ = "vulnerabilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    cve_id: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cvss_score: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="open")
    known_exploited: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    kev_date_added: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    kev_due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    known_ransomware_use: Mapped[bool] = mapped_column(Boolean, default=False)
    affected_product: Mapped[str | None] = mapped_column(String(240), nullable=True)
    cwe_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    required_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[str] = mapped_column(String(100), default="NVD")
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    asset: Mapped[Asset] = relationship(back_populates="vulnerabilities")

    @property
    def composite_risk_priority(self) -> str:
        is_exposed = bool(self.asset and self.asset.internet_exposed)
        is_crit_service = bool(self.asset and self.asset.business_service and self.asset.business_service.criticality.lower() == "critical")
        if self.known_exploited and is_exposed and is_crit_service:
            return "CRITICAL_EXPLOITED_EXPOSED"
        if self.known_exploited and is_exposed:
            return "HIGH_EXPLOITED_EXPOSED"
        if self.known_exploited:
            return "ELEVATED_EXPLOITED"
        if is_exposed and self.severity.upper() == "CRITICAL":
            return "HIGH_EXPOSED_CRITICAL"
        return self.severity.upper()


class Threat(TimestampMixin, Base):
    __tablename__ = "threats"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(60))
    annual_frequency: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
    source: Mapped[str] = mapped_column(String(120))


class Control(TimestampMixin, Base):
    __tablename__ = "controls"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(Text)
    effectiveness: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    status: Mapped[str] = mapped_column(String(30), default="active")
    framework_mappings: Mapped[list["FrameworkControl"]] = relationship(back_populates="master_control")


class Risk(TimestampMixin, Base):
    __tablename__ = "risks"
    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    likelihood: Mapped[Decimal] = mapped_column(Numeric(8, 5))
    financial_impact: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    expected_annual_loss: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0)
    calculation_version: Mapped[str] = mapped_column(String(40), default="baseline-1")
    asset: Mapped[Asset] = relationship(back_populates="risks")


class Investment(TimestampMixin, Base):
    __tablename__ = "investments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str] = mapped_column(Text)
    cost: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    risk_reduction: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    implementation_days: Mapped[int] = mapped_column(default=30)
    status: Mapped[str] = mapped_column(String(30), default="available")


class FrameworkControl(TimestampMixin, Base):
    __tablename__ = "framework_controls"
    id: Mapped[int] = mapped_column(primary_key=True)
    framework: Mapped[str] = mapped_column(String(80), index=True)
    control_code: Mapped[str] = mapped_column(String(80))
    control_name: Mapped[str] = mapped_column(String(200))
    master_control_id: Mapped[int] = mapped_column(ForeignKey("controls.id"))
    master_control: Mapped[Control] = relationship(back_populates="framework_mappings")
