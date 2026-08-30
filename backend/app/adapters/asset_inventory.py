from decimal import Decimal
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.base import BaseSourceAdapter
from app.models.entities import Asset, BusinessService

logger = logging.getLogger(__name__)

# Core anchor assets essential for cross-source correlation scenarios
CORE_ANCHOR_ASSETS: list[dict[str, Any]] = [
    {
        "asset_id_code": "GATEWAY-01",
        "name": "Internet Gateway",
        "asset_type": "network",
        "environment": "production",
        "owner": "Platform",
        "department": "Infrastructure",
        "criticality": "CRITICAL",
        "business_value": Decimal("18000000.00"),
        "internet_exposed": True,
        "hostname": "gw-edge-01.cyberval.net",
        "ip_address": "198.51.100.1",
        "cloud_provider": "on-premise",
        "service_name": "Payment Service",
    },
    {
        "asset_id_code": "PAYMENT-API-01",
        "name": "Payment API",
        "asset_type": "application",
        "environment": "production",
        "owner": "Payments",
        "department": "Engineering",
        "criticality": "CRITICAL",
        "business_value": Decimal("48000000.00"),
        "internet_exposed": True,
        "hostname": "api-pay-prod-01.cyberval.net",
        "ip_address": "10.0.1.50",
        "cloud_provider": "AWS",
        "service_name": "Payment Service",
    },
    {
        "asset_id_code": "CUSTOMER-DB-01",
        "name": "Customer Database",
        "asset_type": "database",
        "environment": "production",
        "owner": "Data Office",
        "department": "Data",
        "criticality": "HIGH",
        "business_value": Decimal("26000000.00"),
        "internet_exposed": False,
        "hostname": "db-cust-primary.internal",
        "ip_address": "10.0.2.10",
        "cloud_provider": "AWS",
        "service_name": "Customer Data Platform",
    },
    {
        "asset_id_code": "PAYMENT-DB-01",
        "name": "Payment Processing DB",
        "asset_type": "database",
        "environment": "production",
        "owner": "Payments",
        "department": "Engineering",
        "criticality": "CRITICAL",
        "business_value": Decimal("60000000.00"),
        "internet_exposed": False,
        "hostname": "db-pay-cluster-01.internal",
        "ip_address": "10.0.2.20",
        "cloud_provider": "AWS",
        "service_name": "Payment Service",
    },
    {
        "asset_id_code": "S3-CUSTOMER-DATA",
        "name": "Customer Data S3 Storage",
        "asset_type": "cloud",
        "environment": "production",
        "owner": "Data Office",
        "department": "Data",
        "criticality": "HIGH",
        "business_value": Decimal("20000000.00"),
        "internet_exposed": True,
        "hostname": "s3-customer-data-cyberval.s3.amazonaws.com",
        "ip_address": "52.216.100.12",
        "cloud_provider": "AWS",
        "service_name": "Customer Data Platform",
    },
    {
        "asset_id_code": "AUTH-SERVER-01",
        "name": "Active Directory & SSO Server",
        "asset_type": "identity",
        "environment": "production",
        "owner": "Security",
        "department": "SecOps",
        "criticality": "CRITICAL",
        "business_value": Decimal("35000000.00"),
        "internet_exposed": False,
        "hostname": "ad-dc-01.corp.cyberval.net",
        "ip_address": "10.0.0.5",
        "cloud_provider": "on-premise",
        "service_name": None,
    },
]


class AssetInventorySimulator:
    """Deterministic generator for realistic enterprise asset inventory."""

    @classmethod
    def generate(cls, count: int = 100) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = [dict(a) for a in CORE_ANCHOR_ASSETS]
        
        categories = [
            ("NET", "network", ["Core-Switch", "Edge-Router", "Corporate-VPN-Gateway", "WAF-Appliance", "Branch-Router"], ["Infrastructure", "Networking"], ["LOW", "MEDIUM", "HIGH"], [True, False], ["on-premise", "AWS", "Azure"]),
            ("APP", "application", ["Customer-Portal", "HR-Management-Portal", "Billing-Service", "Notification-Service", "Order-Processor", "Analytics-Dashboard", "Internal-Wiki"], ["Engineering", "Product", "Operations"], ["MEDIUM", "HIGH", "CRITICAL"], [True, False], ["AWS", "GCP", "Azure"]),
            ("DB", "database", ["Analytics-Warehouse", "Redis-Session-Store", "Kafka-Broker", "HR-Database", "Audit-Log-Database", "Search-Elastic-Cluster"], ["Data", "Engineering", "IT"], ["MEDIUM", "HIGH", "CRITICAL"], [False], ["AWS", "Azure", "on-premise"]),
            ("CLOUD", "cloud", ["K8s-Worker-Node", "Lambda-Pay-Processor", "CloudTrail-Bucket", "VPC-Peering-Router", "EKS-Control-Plane", "RDS-Read-Replica"], ["DevOps", "CloudOps"], ["LOW", "MEDIUM", "HIGH", "CRITICAL"], [False, True], ["AWS", "GCP"]),
            ("ID", "identity", ["IAM-OIDC-Provider", "LDAP-Directory-Replica", "Vault-Secrets-Manager", "Okta-Gateway-Sync"], ["SecOps", "IT"], ["HIGH", "CRITICAL"], [False], ["on-premise", "AWS"]),
            ("EP", "endpoint", ["SecOps-Admin-Workstation", "DevOps-Bastion-Host", "Finance-Lead-Laptop", "Executive-Workstation", "Build-Agent-Runner"], ["IT", "DevOps", "Security"], ["LOW", "MEDIUM", "HIGH"], [False], ["on-premise"]),
        ]

        index = len(assets) + 1
        cat_idx = 0
        while len(assets) < max(count, len(CORE_ANCHOR_ASSETS)):
            prefix, asset_type, name_templates, depts, crits, exposures, providers = categories[cat_idx % len(categories)]
            template_name = name_templates[(index - 1) % len(name_templates)]
            dept = depts[(index - 1) % len(depts)]
            crit = crits[(index - 1) % len(crits)]
            exposed = exposures[(index - 1) % len(exposures)]
            provider = providers[(index - 1) % len(providers)]

            code = f"{prefix}-{index:03d}"
            name = f"{template_name} {index:02d}"
            val_mult = {"LOW": 100000, "MEDIUM": 800000, "HIGH": 4500000, "CRITICAL": 15000000}.get(crit, 500000)
            val = Decimal(str(val_mult + (index * 25000)))

            subnet = 10 if not exposed else 198
            third = (index * 7) % 250 + 1
            ip = f"{subnet}.{index % 4}.{third}.{index % 254 + 1}"
            host = f"{name.lower().replace(' ', '-')}.internal" if not exposed else f"{name.lower().replace(' ', '-')}.cyberval.net"

            assets.append({
                "asset_id_code": code,
                "name": name,
                "asset_type": asset_type,
                "environment": "production" if index % 5 != 0 else "staging",
                "owner": f"{dept} Team",
                "department": dept,
                "criticality": crit,
                "business_value": val,
                "internet_exposed": exposed,
                "hostname": host,
                "ip_address": ip,
                "cloud_provider": provider,
                "service_name": "Payment Service" if "Pay" in name else ("Customer Data Platform" if "Cust" in name else None),
            })
            index += 1
            cat_idx += 1

        return assets[:count]


class AssetInventoryAdapter(BaseSourceAdapter):
    """Adapter for ingesting and normalizing enterprise asset inventory."""

    @property
    def source_name(self) -> str:
        return "asset_inventory"

    def fetch(self, count: int = 100, **kwargs) -> list[dict[str, Any]]:
        return AssetInventorySimulator.generate(count=count)

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for r in raw_records:
            code = r.get("asset_id_code") or r.get("asset_id") or r.get("id_code")
            name = r.get("name") or code or "Unnamed Asset"
            crit = str(r.get("criticality", "medium")).upper()
            val = Decimal(str(r.get("business_value", 0)))
            normalized.append({
                "asset_id_code": code.strip().upper() if code else None,
                "name": name.strip(),
                "asset_type": str(r.get("asset_type", "unknown")).lower(),
                "environment": str(r.get("environment", "production")).lower(),
                "owner": str(r.get("owner", "unassigned")).strip(),
                "department": str(r.get("department", "Engineering")).strip(),
                "criticality": crit if crit in ("LOW", "MEDIUM", "HIGH", "CRITICAL") else "MEDIUM",
                "business_value": val,
                "internet_exposed": bool(r.get("internet_exposed", False)),
                "hostname": r.get("hostname"),
                "ip_address": r.get("ip_address"),
                "cloud_provider": r.get("cloud_provider", "on-premise"),
                "status": str(r.get("status", "active")).lower(),
                "service_name": r.get("service_name"),
            })
        return normalized

    def validate(self, normalized_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        valid: list[dict[str, Any]] = []
        for r in normalized_records:
            if r.get("name"):
                valid.append(r)
        return valid

    def ingest(self, db: Session, records: list[dict[str, Any]] | None = None, count: int = 100, **kwargs) -> int:
        if records is None:
            raw = self.fetch(count=count)
        else:
            raw = records

        normalized = self.normalize(raw)
        validated = self.validate(normalized)

        # Pre-fetch existing services to resolve references
        services = {s.name: s.id for s in db.scalars(select(BusinessService)).all()}

        ingested_count = 0
        for item in validated:
            code = item["asset_id_code"]
            name = item["name"]

            # Lookup by asset_id_code or name to avoid duplicating existing seeded assets
            asset = None
            if code:
                asset = db.scalar(select(Asset).where(Asset.asset_id_code == code))
            if not asset:
                asset = db.scalar(select(Asset).where(Asset.name == name))

            if not asset:
                asset = Asset(name=name)
                db.add(asset)

            asset.asset_id_code = code or asset.asset_id_code
            asset.name = name
            asset.asset_type = item["asset_type"]
            asset.environment = item["environment"]
            asset.owner = item["owner"]
            asset.department = item["department"]
            asset.criticality = item["criticality"]
            asset.business_value = item["business_value"]
            asset.internet_exposed = item["internet_exposed"]
            asset.hostname = item["hostname"]
            asset.ip_address = item["ip_address"]
            asset.cloud_provider = item["cloud_provider"]
            asset.status = item["status"]

            # Map business service if matching
            svc_name = item.get("service_name")
            if svc_name and svc_name in services:
                asset.business_service_id = services[svc_name]

            ingested_count += 1

        db.commit()
        return ingested_count
