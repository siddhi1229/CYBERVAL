from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import Asset, SecurityEvent, Threat, Vulnerability


class NormalizedIngestionService:
    """Maps supported telemetry records into shared SQLAlchemy entities."""

    def ingest(self, db: Session, source: str, records: Iterable[dict[str, Any]]) -> int:
        handlers = {
            "asset_inventory": self._asset,
            "vulnerability_scanner": self._vulnerability,
            "threat_intelligence": self._threat,
            "siem": self._security_event,
            "iam": self._security_event,
            "edr": self._security_event,
            "cspm": self._security_event,
        }
        handler = handlers.get(source)
        if handler is None:
            raise ValueError(f"Unsupported telemetry source: {source}")
        count = 0
        for record in records:
            db.add(handler(record))
            count += 1
        db.commit()
        return count

    @staticmethod
    def _asset(record: dict[str, Any]) -> Asset:
        return Asset(name=record["name"], asset_type=record.get("asset_type", "unknown"), environment=record.get("environment", "production"), owner=record.get("owner", "unassigned"), internet_exposed=bool(record.get("internet_exposed", False)))

    @staticmethod
    def _vulnerability(record: dict[str, Any]) -> Vulnerability:
        return Vulnerability(cve_id=record["cve_id"], title=record.get("title", record["cve_id"]), cvss_score=record.get("cvss_score", 0), severity=record.get("severity", "unknown"), status=record.get("status", "open"), asset_id=record["asset_id"])

    @staticmethod
    def _threat(record: dict[str, Any]) -> Threat:
        return Threat(name=record["name"], category=record.get("category", "unknown"), annual_frequency=record.get("annual_frequency", 0), source=record.get("source", "synthetic"))

    @staticmethod
    def _security_event(record: dict[str, Any]) -> SecurityEvent:
        return SecurityEvent(source=record.get("source", "synthetic"), event_type=record["event_type"], severity=record.get("severity", "info"), observed_at=record.get("observed_at", datetime.now(UTC)), asset_id=record.get("asset_id"), raw_payload=str(record))
