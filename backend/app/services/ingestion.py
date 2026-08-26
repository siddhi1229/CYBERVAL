from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters import (
    AssetInventoryAdapter,
    CSPMAdapter,
    EDRAdapter,
    IAMAdapter,
    SIEMAdapter,
)
from app.models import Asset, CveCatalogRecord, SecurityEvent, Threat, User, Vulnerability
from app.services.correlator import CveCorrelatorService


class NormalizedIngestionService:
    """Maps supported telemetry and inventory records into shared SQLAlchemy entities with CVE correlation and adapter support."""

    def __init__(self, correlator: CveCorrelatorService | None = None):
        self.correlator = correlator or CveCorrelatorService()
        self.asset_adapter = AssetInventoryAdapter()
        self.iam_adapter = IAMAdapter()
        self.siem_adapter = SIEMAdapter()
        self.edr_adapter = EDRAdapter()
        self.cspm_adapter = CSPMAdapter()

    def ingest(self, db: Session, source: str, records: Iterable[dict[str, Any]]) -> int:
        records_list = list(records)
        
        # Modular adapter handlers
        if source == "asset_inventory":
            return self.asset_adapter.ingest(db, records=records_list)
        if source == "iam":
            return self.iam_adapter.ingest(db, records=records_list)
        if source == "siem":
            return self.siem_adapter.ingest(db, records=records_list)
        if source == "edr":
            return self.edr_adapter.ingest(db, records=records_list)
        if source == "cspm":
            return self.cspm_adapter.ingest(db, records=records_list)

        handlers = {
            "vulnerability_scanner": lambda r: self._vulnerability(db, r),
            "threat_intelligence": lambda r: self._threat(r),
            "nvd": lambda r: self._nvd_record(db, r),
            "cisa_kev": lambda r: self._cisa_kev_record(db, r),
            "cve_catalog": lambda r: self._cve_catalog_record(db, r),
        }
        handler = handlers.get(source)
        if handler is None:
            raise ValueError(f"Unsupported telemetry source: {source}")
        count = 0
        for record in records_list:
            entity = handler(record)
            if entity:
                db.add(entity)
                count += 1
        db.commit()
        return count

    def sync_enterprise(
        self,
        db: Session,
        asset_count: int = 100,
        user_count: int = 35,
        siem_count: int = 120,
        edr_count: int = 60,
        cspm_count: int = 35,
    ) -> dict[str, Any]:
        """Orchestrates ingestion across all 5 simulated sources into normalized PostgreSQL entities."""
        # 1. Asset Inventory
        assets_ingested = self.asset_adapter.ingest(db, count=asset_count)

        # 2. IAM Identities & Access
        iam_ingested = self.iam_adapter.ingest(db, count=user_count)

        # Count IAM access relationships
        from app.models.entities import UserAssetAccess
        iam_access_cnt = db.query(UserAssetAccess).count()

        # 3. SIEM Security Events
        siem_ingested = self.siem_adapter.ingest(db, count=siem_count)

        # 4. EDR Endpoint Events
        edr_ingested = self.edr_adapter.ingest(db, count=edr_count)

        # 5. CSPM Posture Findings
        cspm_ingested = self.cspm_adapter.ingest(db, count=cspm_count)

        # 6. Auto-enrich existing asset vulnerabilities with NVD + CISA KEV
        self.correlator.enrich_asset_vulnerabilities(db)

        # Verify high risk scenario on PAYMENT-API-01 & USR-001
        pay_api = db.scalar(select(Asset).where(Asset.asset_id_code == "PAYMENT-API-01"))
        admin_u = db.scalar(select(User).where(User.user_id_code == "USR-001"))
        high_risk_confirmed = bool(
            pay_api
            and pay_api.internet_exposed
            and admin_u
            and not admin_u.mfa_enabled
            and admin_u.failed_login_count >= 10
        )

        return {
            "assets_count": assets_ingested,
            "iam_users_count": iam_ingested,
            "iam_access_count": iam_access_cnt,
            "siem_events_count": siem_ingested,
            "edr_events_count": edr_ingested,
            "cspm_findings_count": cspm_ingested,
            "high_risk_scenario_confirmed": high_risk_confirmed,
            "timestamp": datetime.now(UTC),
        }

    @staticmethod
    def _asset(record: dict[str, Any]) -> Asset:
        return Asset(
            name=record["name"],
            asset_type=record.get("asset_type", "unknown"),
            environment=record.get("environment", "production"),
            owner=record.get("owner", "unassigned"),
            internet_exposed=bool(record.get("internet_exposed", False)),
        )

    def _vulnerability(self, db: Session, record: dict[str, Any]) -> Vulnerability:
        cve_id = record["cve_id"].strip().upper()
        catalog_entry = db.get(CveCatalogRecord, cve_id)

        title = record.get("title") or (catalog_entry.title if catalog_entry else cve_id)
        description = record.get("description") or (catalog_entry.description if catalog_entry else None)
        cvss_score = Decimal(str(record.get("cvss_score") or (catalog_entry.cvss_score if catalog_entry else "0.0")))
        severity = str(record.get("severity") or (catalog_entry.severity if catalog_entry else "unknown")).lower()
        known_exploited = bool(record.get("known_exploited", catalog_entry.known_exploited if catalog_entry else False))
        kev_date_added = record.get("kev_date_added") or (catalog_entry.kev_date_added if catalog_entry else None)
        kev_due_date = record.get("kev_due_date") or (catalog_entry.kev_due_date if catalog_entry else None)
        known_ransomware = bool(record.get("known_ransomware_use", catalog_entry.known_ransomware_campaign_use if catalog_entry else False))
        affected_product = record.get("affected_product") or (catalog_entry.affected_product if catalog_entry else None)
        cwe_id = record.get("cwe_id") or (catalog_entry.cwe_ids if catalog_entry else None)
        required_action = record.get("required_action") or (catalog_entry.required_action if catalog_entry else None)
        sources = record.get("sources") or (catalog_entry.sources if catalog_entry else "vulnerability_scanner")

        return Vulnerability(
            cve_id=cve_id,
            title=title[:300],
            description=description,
            cvss_score=cvss_score,
            severity=severity,
            status=record.get("status", "open"),
            asset_id=int(record["asset_id"]),
            known_exploited=known_exploited,
            kev_date_added=kev_date_added,
            kev_due_date=kev_due_date,
            known_ransomware_use=known_ransomware,
            affected_product=affected_product,
            cwe_id=cwe_id,
            required_action=required_action,
            sources=sources,
        )

    def _nvd_record(self, db: Session, record: dict[str, Any]) -> CveCatalogRecord:
        parsed = self.correlator.nvd.parse_nvd_item(record) if "cve" in record else record
        cve_id = parsed["cve_id"].strip().upper()
        existing = db.get(CveCatalogRecord, cve_id)
        if not existing:
            existing = CveCatalogRecord(cve_id=cve_id)
        existing.title = parsed.get("title", f"Vulnerability {cve_id}")[:300]
        existing.description = parsed.get("description")
        existing.cvss_score = Decimal(str(parsed.get("cvss_score", "0.0")))
        existing.severity = str(parsed.get("severity", "UNKNOWN")).upper()
        existing.cvss_vector = parsed.get("cvss_vector")
        existing.affected_vendor = parsed.get("affected_vendor")
        existing.affected_product = parsed.get("affected_product")
        existing.cwe_ids = parsed.get("cwe_ids")
        existing.required_action = parsed.get("required_action")
        existing.sources = "NVD" if "NVD" in existing.sources else f"{existing.sources},NVD"
        return existing

    def _cisa_kev_record(self, db: Session, record: dict[str, Any]) -> CveCatalogRecord:
        cve_id = (record.get("cveID") or record.get("cve_id", "")).strip().upper()
        existing = db.get(CveCatalogRecord, cve_id)
        if not existing:
            existing = CveCatalogRecord(cve_id=cve_id)
        existing.title = record.get("vulnerabilityName", record.get("title", f"Vulnerability {cve_id}"))[:300]
        existing.description = record.get("shortDescription", record.get("description"))
        existing.known_exploited = True
        date_added = record.get("dateAdded") or record.get("date_added")
        if isinstance(date_added, str):
            try:
                date_added = datetime.strptime(date_added, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                date_added = None
        existing.kev_date_added = date_added

        due_date = record.get("dueDate") or record.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                due_date = None
        existing.kev_due_date = due_date

        ransomware = record.get("knownRansomwareCampaignUse") or record.get("known_ransomware_campaign_use")
        existing.known_ransomware_campaign_use = str(ransomware).lower() in ("known", "true", "1")
        existing.affected_vendor = record.get("vendorProject", record.get("affected_vendor"))
        existing.affected_product = record.get("product", record.get("affected_product"))
        existing.required_action = record.get("requiredAction", record.get("required_action"))
        existing.sources = "CISA_KEV" if "CISA_KEV" in existing.sources else f"{existing.sources},CISA_KEV"
        return existing

    @staticmethod
    def _cve_catalog_record(db: Session, record: dict[str, Any]) -> CveCatalogRecord:
        cve_id = record["cve_id"].strip().upper()
        existing = db.get(CveCatalogRecord, cve_id)
        if not existing:
            existing = CveCatalogRecord(cve_id=cve_id)
        for field in ("title", "description", "cvss_vector", "affected_vendor", "affected_product", "cwe_ids", "required_action", "sources"):
            if field in record:
                setattr(existing, field, record[field])
        if "cvss_score" in record:
            existing.cvss_score = Decimal(str(record["cvss_score"]))
        if "severity" in record:
            existing.severity = str(record["severity"]).upper()
        if "known_exploited" in record:
            existing.known_exploited = bool(record["known_exploited"])
        if "known_ransomware_campaign_use" in record:
            existing.known_ransomware_campaign_use = bool(record["known_ransomware_campaign_use"])
        return existing

    @staticmethod
    def _threat(record: dict[str, Any]) -> Threat:
        return Threat(
            name=record["name"],
            category=record.get("category", "unknown"),
            annual_frequency=record.get("annual_frequency", 0),
            source=record.get("source", "synthetic"),
        )

    @staticmethod
    def _security_event(record: dict[str, Any]) -> SecurityEvent:
        return SecurityEvent(
            source=record.get("source", "synthetic"),
            event_type=record["event_type"],
            severity=record.get("severity", "info"),
            observed_at=record.get("observed_at", datetime.now(UTC)),
            asset_id=record.get("asset_id"),
            raw_payload=str(record),
        )
