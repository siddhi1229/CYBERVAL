"""CYBERVAL P2 - Cyber Risk Quantification Engine.

Converts P1 normalized security telemetry (PostgreSQL) into financial cyber risk:
risk signals -> likelihood -> financial impact -> Expected Annual Loss ->
Monte Carlo simulation -> P50/P90/P95/P99 / VaR -> risk drivers -> enterprise risk.

This module is strictly a *consumer* of P1 data. It creates no new datasets and
does not re-implement ingestion. The only schema addition is the append-only
``risk_history`` table (see ``app/models/risk_history.py``) which is required to
serve historical risk trends.
"""

from app.services.risk.config import RiskEngineConfig, get_default_config
from app.services.risk.engine import RiskEngine

__all__ = ["RiskEngine", "RiskEngineConfig", "get_default_config"]
