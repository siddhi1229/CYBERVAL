"""P2 schema addition: append-only risk calculation history.

RATIONALE (documented per the P2 brief's "document every schema modification"):
``GET /api/risk/trends`` must return how risk has moved over time. P1 has no
time-series store - the ``risks`` table holds one current row per asset. Rather
than overload ``risks`` (which ``/api/risk/enterprise`` sums, so extra rows
would double-count), P2 adds a single dedicated, append-only table.

This table:
  * is written only by ``POST /api/risk/calculate`` (one snapshot row per scope
    per run);
  * is never updated or deleted by the engine;
  * does not modify, reference-constrain, or alter any P1 table;
  * is created automatically by ``Base.metadata.create_all`` (same mechanism P1
    uses in ``init_db.py`` and the test fixtures) - no migration tooling needed.

No P1 model or table is changed. This is the only schema change P2 makes.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    # "asset" | "business_service" | "department" | "enterprise"
    scope: Mapped[str] = mapped_column(String(30), index=True)
    # asset_id (as str), service name, department name, or "enterprise"
    scope_ref: Mapped[str] = mapped_column(String(160), index=True)
    scope_label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    risk_score: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    likelihood_score: Mapped[float] = mapped_column(Numeric(6, 5), default=0)
    annual_incident_probability: Mapped[float] = mapped_column(Numeric(6, 5), default=0)
    financial_impact: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    expected_annual_loss: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    control_effectiveness: Mapped[float] = mapped_column(Numeric(6, 5), default=0)
    residual_expected_annual_loss: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    p95_loss: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    p99_loss: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    var95: Mapped[float] = mapped_column(Numeric(20, 2), default=0)
    var99: Mapped[float] = mapped_column(Numeric(20, 2), default=0)

    calculation_version: Mapped[str] = mapped_column(String(40), default="p2-risk-engine-1.0")
    run_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


Index("ix_risk_history_scope_ref_created", RiskHistory.scope, RiskHistory.scope_ref, RiskHistory.created_at)
