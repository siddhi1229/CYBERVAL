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
    name: Mapped[str] = mapped_column(String(160), index=True)
    asset_type: Mapped[str] = mapped_column(String(60))
    environment: Mapped[str] = mapped_column(String(40), default="production")
    owner: Mapped[str] = mapped_column(String(160))
    internet_exposed: Mapped[bool] = mapped_column(Boolean, default=False)
    business_service_id: Mapped[int | None] = mapped_column(ForeignKey("business_services.id"))
    business_service: Mapped[BusinessService | None] = relationship(back_populates="assets")
    vulnerabilities: Mapped[list["Vulnerability"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    risks: Mapped[list["Risk"]] = relationship(back_populates="asset", cascade="all, delete-orphan")
    security_events: Mapped[list["SecurityEvent"]] = relationship(back_populates="asset")


class Vulnerability(TimestampMixin, Base):
    __tablename__ = "vulnerabilities"
    id: Mapped[int] = mapped_column(primary_key=True)
    cve_id: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(240))
    cvss_score: Mapped[Decimal] = mapped_column(Numeric(4, 1))
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30), default="open")
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    asset: Mapped[Asset] = relationship(back_populates="vulnerabilities")


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


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(240), unique=True)
    display_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(60))
    privileged: Mapped[bool] = mapped_column(Boolean, default=False)


class SecurityEvent(TimestampMixin, Base):
    __tablename__ = "security_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(60))
    event_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[str] = mapped_column(String(20))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"))
    raw_payload: Mapped[str] = mapped_column(Text, default="{}")
    asset: Mapped[Asset | None] = relationship(back_populates="security_events")


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
