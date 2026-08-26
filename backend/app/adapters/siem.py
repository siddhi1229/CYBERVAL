from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import BaseSourceAdapter
from app.models.entities import Asset, SecurityEvent, User

logger = logging.getLogger(__name__)

CORE_SIEM_SCENARIO_EVENTS: list[dict[str, Any]] = [
    {
        "event_id_code": "SIEM-001",
        "source": "SIEM",
        "event_type": "BRUTE_FORCE",
        "asset_id_code": "PAYMENT-API-01",
        "user_id_code": "USR-001",
        "username": "admin.singh",
        "source_ip": "185.10.20.30",
        "technique": "T1110",
        "severity": "critical",
        "description": "Repeated failed authentication attempts exceeding threshold (17 attempts) against Payment API.",
        "minutes_ago": 12,
        "metadata": {"failed_attempts": 17, "target_endpoint": "/api/v1/auth/admin", "user_agent": "Hydra/9.5"},
    },
    {
        "event_id_code": "SIEM-002",
        "source": "SIEM",
        "event_type": "FAILED_LOGIN",
        "asset_id_code": "PAYMENT-API-01",
        "user_id_code": "USR-001",
        "username": "admin.singh",
        "source_ip": "185.10.20.30",
        "technique": "T1110.001",
        "severity": "high",
        "description": "Password spray authentication failure for admin.singh without MFA.",
        "minutes_ago": 15,
        "metadata": {"reason": "invalid_credentials", "mfa_prompted": False},
    },
    {
        "event_id_code": "SIEM-003",
        "source": "SIEM",
        "event_type": "PORT_SCAN",
        "asset_id_code": "GATEWAY-01",
        "user_id_code": None,
        "username": None,
        "source_ip": "45.33.32.156",
        "technique": "T1046",
        "severity": "high",
        "description": "SYN stealth port scan detected targeting exposed ports 443, 8443, 8080, 22 on Internet Gateway.",
        "minutes_ago": 25,
        "metadata": {"ports_probed": [443, 8443, 8080, 22, 21, 3389], "scanner": "Masscan"},
    },
    {
        "event_id_code": "SIEM-004",
        "source": "SIEM",
        "event_type": "UNUSUAL_OUTBOUND_CONNECTION",
        "asset_id_code": "PAYMENT-API-01",
        "user_id_code": "USR-001",
        "username": "admin.singh",
        "source_ip": "10.0.1.50",
        "technique": "T1071.001",
        "severity": "critical",
        "description": "Outbound connection to known malicious C2 IP 194.26.29.11 over HTTPS port 8443.",
        "minutes_ago": 8,
        "metadata": {"destination_ip": "194.26.29.11", "destination_port": 8443, "bytes_sent": 142050},
    },
    {
        "event_id_code": "SIEM-005",
        "source": "SIEM",
        "event_type": "PRIVILEGE_ESCALATION",
        "asset_id_code": "CUSTOMER-DB-01",
        "user_id_code": "USR-001",
        "username": "admin.singh",
        "source_ip": "10.0.1.50",
        "technique": "T1068",
        "severity": "critical",
        "description": "Unauthorized role assumption attempted from Payment API worker to root database schema.",
        "minutes_ago": 6,
        "metadata": {"requested_role": "pg_superuser", "current_role": "payment_app"},
    },
]


class SIEMSimulator:
    """Deterministic generator for realistic SIEM security event telemetry."""

    @classmethod
    def generate(cls, count: int = 120) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = [dict(e) for e in CORE_SIEM_SCENARIO_EVENTS]

        templates = [
            ("FAILED_LOGIN", "medium", "T1110", "Failed user authentication attempt.", ["NET", "APP", "EP"]),
            ("SUSPICIOUS_PROCESS", "high", "T1059", "Execution of scripting interpreter with encoded command line.", ["APP", "EP", "CLOUD"]),
            ("MALWARE_DETECTION", "critical", "T1204", "Heuristic signature detected potential trojan or dropper payload.", ["EP", "APP"]),
            ("PORT_SCAN", "low", "T1046", "Horizontal connection sweep observed across internal subnet.", ["NET", "CLOUD"]),
            ("UNUSUAL_OUTBOUND_CONNECTION", "high", "T1071", "High-volume data transfer to unclassified external IP address.", ["APP", "DB", "CLOUD"]),
            ("PRIVILEGE_ESCALATION", "high", "T1548", "Local token manipulation or sudo elevation detected.", ["APP", "DB", "EP"]),
        ]

        now = datetime.now(UTC)
        index = len(events) + 1
        t_idx = 0
        while len(events) < max(count, len(CORE_SIEM_SCENARIO_EVENTS)):
            etype, sev, tech, desc, allowed_types = templates[t_idx % len(templates)]
            code = f"SIEM-{index:03d}"
            asset_code = "PAYMENT-API-01" if index % 8 == 0 else f"{allowed_types[index % len(allowed_types)]}-{index % 25 + 1:03d}"
            user_code = "USR-001" if index % 9 == 0 else f"USR-{index % 30 + 1:03d}"
            ip = f"192.168.{index % 5}.{index % 250 + 1}" if sev != "critical" else f"185.10.{(index * 3) % 250}.{index % 250 + 1}"
            mins = (index * 13) % 2880  # within last 48 hours

            events.append({
                "event_id_code": code,
                "source": "SIEM",
                "event_type": etype,
                "asset_id_code": asset_code,
                "user_id_code": user_code,
                "username": f"user.{user_code.lower()}",
                "source_ip": ip,
                "technique": tech,
                "severity": sev,
                "description": f"{desc} Observed on asset {asset_code}.",
                "minutes_ago": mins,
                "metadata": {"simulated": True, "event_seq": index},
            })
            index += 1
            t_idx += 1

        return events[:count]


class SIEMAdapter(BaseSourceAdapter):
    """Adapter for ingesting and normalizing SIEM security events."""

    @property
    def source_name(self) -> str:
        return "siem"

    def fetch(self, count: int = 120, **kwargs) -> list[dict[str, Any]]:
        return SIEMSimulator.generate(count=count)

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        now = datetime.now(UTC)
        normalized: list[dict[str, Any]] = []

        for r in raw_records:
            mins = r.get("minutes_ago", 0)
            observed_at = r.get("observed_at") or (now - timedelta(minutes=mins))
            if isinstance(observed_at, str):
                try:
                    observed_at = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
                except ValueError:
                    observed_at = now

            code = r.get("event_id_code") or r.get("event_id") or f"SIEM-{len(normalized) + 1:03d}"
            asset_code = r.get("asset_id_code") or r.get("asset_id")
            user_code = r.get("user_id_code") or r.get("user_id")

            normalized.append({
                "event_id_code": str(code).strip().upper(),
                "source": "SIEM",
                "event_type": str(r.get("event_type", "SECURITY_ALERT")).strip().upper(),
                "severity": str(r.get("severity", "medium")).lower(),
                "observed_at": observed_at,
                "source_ip": r.get("source_ip"),
                "technique": r.get("technique"),
                "description": str(r.get("description", "SIEM Security Event")).strip(),
                "asset_id_code": str(asset_code).strip().upper() if asset_code else None,
                "user_id_code": str(user_code).strip().upper() if user_code else None,
                "metadata": r.get("metadata", {}),
            })
        return normalized

    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        for r in normalized_records:
            if r.get("event_type") and r.get("observed_at"):
                valid.append(r)
        return valid

    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, count: int = 120, **kwargs) -> int:
        if records is None:
            raw = self.fetch(count=count)
        else:
            raw = records

        normalized = self.normalize(raw)
        validated = self.validate(normalized)

        # Pre-fetch existing assets and users to map business codes to database integer PKs
        assets_map: dict[str, int] = {}
        for a in db.scalars(select(Asset)).all():
            if a.asset_id_code:
                assets_map[a.asset_id_code.upper()] = a.id
            assets_map[a.name.upper()] = a.id

        users_map: dict[str, int] = {}
        for u in db.scalars(select(User)).all():
            if u.user_id_code:
                users_map[u.user_id_code.upper()] = u.id
            if u.username:
                users_map[u.username.upper()] = u.id
            users_map[u.email.upper()] = u.id

        ingested_count = 0
        for item in validated:
            asset_db_id = None
            if item.get("asset_id_code"):
                asset_db_id = assets_map.get(item["asset_id_code"])

            user_db_id = None
            if item.get("user_id_code"):
                user_db_id = users_map.get(item["user_id_code"])

            event = SecurityEvent(
                event_id_code=item["event_id_code"],
                source="SIEM",
                event_type=item["event_type"],
                severity=item["severity"],
                observed_at=item["observed_at"],
                source_ip=item["source_ip"],
                technique=item["technique"],
                description=item["description"],
                user_id_code=item["user_id_code"],
                user_id=user_db_id,
                asset_id=asset_db_id,
                raw_payload=json.dumps(item.get("metadata", {}), default=str),
            )
            db.add(event)
            ingested_count += 1

        db.commit()
        return ingested_count
