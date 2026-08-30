import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import BaseSourceAdapter
from app.models.entities import Asset, CspmFinding

logger = logging.getLogger(__name__)

CORE_CSPM_SCENARIO_FINDINGS: list[dict[str, Any]] = [
    {
        "finding_id_code": "CSPM-001",
        "provider": "AWS",
        "resource_id": "S3-CUSTOMER-DATA",
        "resource_type": "S3",
        "finding_type": "PUBLIC_S3_BUCKET",
        "severity": "critical",
        "internet_exposed": True,
        "encrypted": False,
        "description": "Customer Data S3 bucket has public ACL permissions enabled and default encryption disabled.",
        "remediation": "Enable AWS S3 Block Public Access at the account and bucket level; enforce SSE-KMS default encryption.",
    },
    {
        "finding_id_code": "CSPM-002",
        "provider": "AWS",
        "resource_id": "PAYMENT-API-01",
        "resource_type": "SECURITY_GROUP",
        "finding_type": "OPEN_SECURITY_GROUP",
        "severity": "critical",
        "internet_exposed": True,
        "encrypted": True,
        "description": "Security group attached to Payment API instance allows unrestricted inbound traffic (0.0.0.0/0) on management and debug ports.",
        "remediation": "Remove inbound rule 0.0.0.0/0 on ports 22, 8080, and 8443; restrict ingress to approved WAF security group.",
    },
    {
        "finding_id_code": "CSPM-003",
        "provider": "AWS",
        "resource_id": "PAYMENT-DB-01",
        "resource_type": "RDS",
        "finding_type": "RDS_ENCRYPTION_DISABLED",
        "severity": "high",
        "internet_exposed": False,
        "encrypted": False,
        "description": "Production Payment Processing RDS instance is running without KMS storage encryption enabled.",
        "remediation": "Take snapshot, copy with AWS KMS encryption enabled, and restore database instance with encrypted volume.",
    },
    {
        "finding_id_code": "CSPM-004",
        "provider": "AWS",
        "resource_id": "AUTH-SERVER-01",
        "resource_type": "IAM_ROLE",
        "finding_type": "OVERPRIVILEGED_IAM_ROLE",
        "severity": "critical",
        "internet_exposed": False,
        "encrypted": True,
        "description": "IAM role assumed by authentication gateway contains wildcard '*' permissions without boundary conditions.",
        "remediation": "Replace AdministratorAccess policy with scoped least-privilege IAM policies and permission boundaries.",
    },
]


class CSPMSimulator:
    """Deterministic generator for realistic Cloud Security Posture Management (CSPM) findings."""

    @classmethod
    def generate(cls, count: int = 35) -> list[dict[str, Any]]:
        findings: list[dict[str, Any]] = [dict(f) for f in CORE_CSPM_SCENARIO_FINDINGS]

        templates = [
            ("AWS", "S3", "PUBLIC_S3_BUCKET", "critical", True, False, "S3 bucket accessible without authentication.", "Enable S3 Block Public Access."),
            ("AWS", "EC2", "PUBLIC_EC2_INSTANCE", "high", True, True, "EC2 instance assigned public IPv4 address in private subnet.", "Associate EC2 instance with private subnet and NAT gateway."),
            ("AWS", "RDS", "RDS_ENCRYPTION_DISABLED", "high", False, False, "Database storage volume unencrypted.", "Enable KMS encryption at rest."),
            ("AWS", "IAM_ROLE", "OVERPRIVILEGED_IAM_ROLE", "critical", False, True, "IAM role allows full admin actions.", "Scope IAM policy down to required services."),
            ("AWS", "CLOUDTRAIL", "CLOUDTRAIL_DISABLED", "medium", False, True, "Multi-region CloudTrail logging is disabled in secondary region.", "Enable multi-region Trail logging."),
            ("Azure", "VPC", "OPEN_SECURITY_GROUP", "high", True, True, "Network Security Group permits open inbound RDP.", "Close port 3389 to internet."),
            ("GCP", "CLOUD", "UNENCRYPTED_STORAGE_BUCKET", "medium", False, False, "Cloud Storage bucket lacks customer-managed encryption key.", "Configure Cloud KMS key encryption."),
        ]

        index = len(findings) + 1
        t_idx = 0
        while len(findings) < max(count, len(CORE_CSPM_SCENARIO_FINDINGS)):
            prov, rtype, ftype, sev, exposed, enc, desc, rem = templates[t_idx % len(templates)]
            code = f"CSPM-{index:03d}"
            res_id = "PAYMENT-API-01" if index % 5 == 0 else f"CLOUD-{index % 10 + 1:03d}"

            findings.append({
                "finding_id_code": code,
                "provider": prov,
                "resource_id": res_id,
                "resource_type": rtype,
                "finding_type": ftype,
                "severity": sev,
                "internet_exposed": exposed,
                "encrypted": enc,
                "description": f"{desc} Detected on resource {res_id}.",
                "remediation": rem,
            })
            index += 1
            t_idx += 1

        return findings[:count]


class CSPMAdapter(BaseSourceAdapter):
    """Adapter for ingesting and normalizing cloud security posture findings."""

    @property
    def source_name(self) -> str:
        return "cspm"

    def fetch(self, count: int = 35, **kwargs) -> list[dict[str, Any]]:
        return CSPMSimulator.generate(count=count)

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for r in raw_records:
            code = r.get("finding_id_code") or r.get("finding_id") or f"CSPM-{len(normalized) + 1:03d}"
            res_id = r.get("resource_id") or r.get("asset_id_code") or r.get("asset_id") or "UNKNOWN-RES"
            ftype = r.get("finding_type") or r.get("finding") or "MISCONFIGURATION"

            normalized.append({
                "finding_id_code": str(code).strip().upper(),
                "provider": str(r.get("provider", "AWS")).strip().upper(),
                "resource_id": str(res_id).strip().upper(),
                "resource_type": str(r.get("resource_type", "CLOUD")).strip().upper(),
                "finding_type": str(ftype).strip().upper(),
                "description": r.get("description"),
                "severity": str(r.get("severity", "medium")).lower(),
                "status": str(r.get("status", "open")).lower(),
                "internet_exposed": bool(r.get("internet_exposed", False)),
                "encrypted": bool(r.get("encrypted", True)),
                "remediation": r.get("remediation"),
                "raw_payload": r,
            })
        return normalized

    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        for r in normalized_records:
            if r.get("finding_type") and r.get("resource_id"):
                valid.append(r)
        return valid

    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, count: int = 35, **kwargs) -> int:
        if records is None:
            raw = self.fetch(count=count)
        else:
            raw = records

        normalized = self.normalize(raw)
        validated = self.validate(normalized)

        # Pre-fetch existing assets to link cloud resources to assets by asset_id_code or name
        assets_map: dict[str, int] = {}
        for a in db.scalars(select(Asset)).all():
            if a.asset_id_code:
                assets_map[a.asset_id_code.upper()] = a.id
            assets_map[a.name.upper()] = a.id

        ingested_count = 0
        for item in validated:
            code = item["finding_id_code"]
            asset_db_id = assets_map.get(item["resource_id"])

            existing = db.scalar(select(CspmFinding).where(CspmFinding.finding_id_code == code))
            if not existing:
                existing = CspmFinding(finding_id_code=code)
                db.add(existing)

            existing.provider = item["provider"]
            existing.resource_id = item["resource_id"]
            existing.resource_type = item["resource_type"]
            existing.finding_type = item["finding_type"]
            existing.description = item["description"]
            existing.severity = item["severity"]
            existing.status = item["status"]
            existing.internet_exposed = item["internet_exposed"]
            existing.encrypted = item["encrypted"]
            existing.remediation = item["remediation"]
            existing.asset_id = asset_db_id
            existing.raw_payload = json.dumps(item.get("raw_payload", {}), default=str)

            ingested_count += 1

        db.commit()
        return ingested_count
