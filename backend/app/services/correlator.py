import json
import logging
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Asset, CveCatalogRecord, Vulnerability
from app.services.cisa_kev import CisaKevClient
from app.services.nvd import NvdClient

logger = logging.getLogger(__name__)


class CveCorrelatorService:
    """Service to correlate NVD vulnerability details with CISA KEV exploitation status."""

    def __init__(self, nvd_client: NvdClient | None = None, kev_client: CisaKevClient | None = None):
        self.nvd = nvd_client or NvdClient()
        self.kev = kev_client or CisaKevClient()

    def correlate_cve(
        self,
        cve_id: str,
        nvd_record: dict[str, Any] | None = None,
        kev_record: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Combine NVD vulnerability metrics and CISA KEV exploitation status into a single normalized record."""
        canonical_cve = cve_id.strip().upper()
        sources: list[str] = []

        if nvd_record:
            sources.append("NVD")
        if kev_record:
            sources.append("CISA_KEV")
        if not sources:
            sources.append("MANUAL")

        # Determine best title & description
        title = ""
        description = None
        if kev_record and kev_record.get("vulnerability_name"):
            title = kev_record["vulnerability_name"]
        elif nvd_record and nvd_record.get("title"):
            title = nvd_record["title"]
        else:
            title = f"Vulnerability {canonical_cve}"

        if nvd_record and nvd_record.get("description"):
            description = nvd_record["description"]
        elif kev_record and kev_record.get("short_description"):
            description = kev_record["short_description"]

        # CVSS Score and Severity from NVD (or heuristic default)
        cvss_score = Decimal("0.0")
        severity = "UNKNOWN"
        cvss_vector = None
        if nvd_record:
            cvss_score = nvd_record.get("cvss_score", Decimal("0.0"))
            severity = nvd_record.get("severity", "UNKNOWN")
            cvss_vector = nvd_record.get("cvss_vector")
        elif kev_record:
            # If in KEV without NVD record yet, default to high severity baseline
            cvss_score = Decimal("8.5")
            severity = "HIGH"

        # Affected product/vendor
        vendor = None
        product = None
        if kev_record and (kev_record.get("vendor_project") or kev_record.get("product")):
            vendor = kev_record.get("vendor_project")
            product = kev_record.get("product")
        elif nvd_record:
            vendor = nvd_record.get("affected_vendor")
            product = nvd_record.get("affected_product")

        # CWEs
        cwes = None
        if nvd_record and nvd_record.get("cwe_ids"):
            cwes = nvd_record.get("cwe_ids")
        elif kev_record and kev_record.get("cwe_ids"):
            cwes = kev_record.get("cwe_ids")

        # Required Action (priority to CISA KEV)
        required_action = None
        if kev_record and kev_record.get("required_action"):
            required_action = kev_record.get("required_action")
        elif nvd_record and nvd_record.get("required_action"):
            required_action = nvd_record.get("required_action")

        raw_payload = {
            "nvd": nvd_record.get("raw_payload") if nvd_record else None,
            "cisa_kev": kev_record.get("raw_item") if kev_record else None,
        }

        return {
            "cve_id": canonical_cve,
            "title": title[:300],
            "description": description,
            "cvss_score": cvss_score,
            "severity": severity.upper(),
            "cvss_vector": cvss_vector,
            "known_exploited": bool(kev_record is not None),
            "kev_date_added": kev_record.get("date_added") if kev_record else None,
            "kev_due_date": kev_record.get("due_date") if kev_record else None,
            "known_ransomware_campaign_use": bool(kev_record.get("known_ransomware_campaign_use", False)) if kev_record else False,
            "affected_vendor": vendor,
            "affected_product": product,
            "cwe_ids": cwes,
            "required_action": required_action,
            "sources": ",".join(sources),
            "raw_data": json.dumps(raw_payload, default=str),
        }

    def sync_catalog(
        self,
        db: Session,
        cve_ids: list[str] | None = None,
        sync_cisa_kev: bool = True,
        sync_nvd: bool = True,
    ) -> tuple[int, int, int]:
        """Fetch, correlate, and persist normalized CVE records in PostgreSQL."""
        kev_map: dict[str, dict[str, Any]] = {}
        kev_count = 0
        if sync_cisa_kev:
            kev_records = self.kev.fetch_catalog()
            kev_count = len(kev_records)
            for r in kev_records:
                kev_map[r["cve_id"].upper()] = r

        # Determine target CVE IDs to correlate
        target_cves: set[str] = set()
        if cve_ids:
            target_cves.update(c.strip().upper() for c in cve_ids if c.strip())
        else:
            # If no explicit list, correlate all existing asset vulnerabilities + top KEV records
            existing_vulns = db.scalars(select(Vulnerability.cve_id)).all()
            target_cves.update(c.strip().upper() for c in existing_vulns)
            # Also include all in kev_map
            target_cves.update(kev_map.keys())

        nvd_count = 0
        correlated_count = 0

        for cve_id in target_cves:
            nvd_rec = None
            if sync_nvd:
                nvd_rec = self.nvd.fetch_cve(cve_id)
                if nvd_rec:
                    nvd_count += 1

            kev_rec = kev_map.get(cve_id)
            if not nvd_rec and not kev_rec:
                continue

            normalized = self.correlate_cve(cve_id, nvd_record=nvd_rec, kev_record=kev_rec)

            # Upsert into CveCatalogRecord
            catalog_item = db.get(CveCatalogRecord, cve_id)
            if not catalog_item:
                catalog_item = CveCatalogRecord(cve_id=cve_id)
                db.add(catalog_item)

            catalog_item.title = normalized["title"]
            catalog_item.description = normalized["description"]
            catalog_item.cvss_score = normalized["cvss_score"]
            catalog_item.severity = normalized["severity"]
            catalog_item.cvss_vector = normalized["cvss_vector"]
            catalog_item.known_exploited = normalized["known_exploited"]
            catalog_item.kev_date_added = normalized["kev_date_added"]
            catalog_item.kev_due_date = normalized["kev_due_date"]
            catalog_item.known_ransomware_campaign_use = normalized["known_ransomware_campaign_use"]
            catalog_item.affected_vendor = normalized["affected_vendor"]
            catalog_item.affected_product = normalized["affected_product"]
            catalog_item.cwe_ids = normalized["cwe_ids"]
            catalog_item.required_action = normalized["required_action"]
            catalog_item.sources = normalized["sources"]
            catalog_item.raw_data = normalized["raw_data"]

            correlated_count += 1

        db.commit()
        return kev_count, nvd_count, correlated_count

    def enrich_asset_vulnerabilities(self, db: Session) -> int:
        """Enrich all asset vulnerabilities using the correlated CVE catalog."""
        vulnerabilities = db.scalars(select(Vulnerability)).all()
        enriched_count = 0

        for vuln in vulnerabilities:
            cve_id = vuln.cve_id.strip().upper()
            cat = db.get(CveCatalogRecord, cve_id)
            if not cat:
                # Try fetching live
                nvd_rec = self.nvd.fetch_cve(cve_id)
                kev_items = self.kev.fetch_catalog()
                kev_rec = next((k for k in kev_items if k["cve_id"].upper() == cve_id), None)
                if nvd_rec or kev_rec:
                    normalized = self.correlate_cve(cve_id, nvd_rec, kev_rec)
                    cat = CveCatalogRecord(
                        cve_id=cve_id,
                        title=normalized["title"],
                        description=normalized["description"],
                        cvss_score=normalized["cvss_score"],
                        severity=normalized["severity"],
                        cvss_vector=normalized["cvss_vector"],
                        known_exploited=normalized["known_exploited"],
                        kev_date_added=normalized["kev_date_added"],
                        kev_due_date=normalized["kev_due_date"],
                        known_ransomware_campaign_use=normalized["known_ransomware_campaign_use"],
                        affected_vendor=normalized["affected_vendor"],
                        affected_product=normalized["affected_product"],
                        cwe_ids=normalized["cwe_ids"],
                        required_action=normalized["required_action"],
                        sources=normalized["sources"],
                        raw_data=normalized["raw_data"],
                    )
                    db.add(cat)
                    db.flush()

            if cat:
                vuln.title = cat.title or vuln.title
                vuln.description = cat.description or vuln.description
                if cat.cvss_score > 0:
                    vuln.cvss_score = cat.cvss_score
                if cat.severity and cat.severity != "UNKNOWN":
                    vuln.severity = cat.severity.lower()
                vuln.known_exploited = cat.known_exploited
                vuln.kev_date_added = cat.kev_date_added
                vuln.kev_due_date = cat.kev_due_date
                vuln.known_ransomware_use = cat.known_ransomware_campaign_use
                vuln.affected_product = cat.affected_product
                vuln.cwe_id = cat.cwe_ids
                vuln.required_action = cat.required_action
                vuln.sources = cat.sources
                enriched_count += 1

        db.commit()
        return enriched_count

    def associate_cve_with_asset(
        self,
        db: Session,
        cve_id: str,
        asset_id: int,
        status: str = "open",
        custom_title: str | None = None,
    ) -> Vulnerability:
        """Associate a normalized CVE with an asset, inheriting KEV and NVD intelligence."""
        canonical_cve = cve_id.strip().upper()
        asset = db.get(Asset, asset_id)
        if not asset:
            raise ValueError(f"Asset with id {asset_id} does not exist.")

        # Check if catalog has it
        cat = db.get(CveCatalogRecord, canonical_cve)
        if not cat:
            # Sync this single CVE
            nvd_rec = self.nvd.fetch_cve(canonical_cve)
            kev_list = self.kev.fetch_catalog()
            kev_rec = next((k for k in kev_list if k["cve_id"].upper() == canonical_cve), None)
            norm = self.correlate_cve(canonical_cve, nvd_rec, kev_rec)
            cat = CveCatalogRecord(
                cve_id=canonical_cve,
                title=norm["title"],
                description=norm["description"],
                cvss_score=norm["cvss_score"],
                severity=norm["severity"],
                cvss_vector=norm["cvss_vector"],
                known_exploited=norm["known_exploited"],
                kev_date_added=norm["kev_date_added"],
                kev_due_date=norm["kev_due_date"],
                known_ransomware_campaign_use=norm["known_ransomware_campaign_use"],
                affected_vendor=norm["affected_vendor"],
                affected_product=norm["affected_product"],
                cwe_ids=norm["cwe_ids"],
                required_action=norm["required_action"],
                sources=norm["sources"],
                raw_data=norm["raw_data"],
            )
            db.add(cat)
            db.flush()

        # Check existing vulnerability on this asset
        vuln = db.scalar(
            select(Vulnerability).where(
                Vulnerability.asset_id == asset_id,
                Vulnerability.cve_id == canonical_cve,
            )
        )

        if not vuln:
            vuln = Vulnerability(
                cve_id=canonical_cve,
                asset_id=asset_id,
                title=custom_title or cat.title or f"Vulnerability {canonical_cve}",
                description=cat.description,
                cvss_score=cat.cvss_score if cat.cvss_score > 0 else Decimal("5.0"),
                severity=cat.severity.lower() if cat.severity and cat.severity != "UNKNOWN" else "medium",
                status=status,
                known_exploited=cat.known_exploited,
                kev_date_added=cat.kev_date_added,
                kev_due_date=cat.kev_due_date,
                known_ransomware_use=cat.known_ransomware_campaign_use,
                affected_product=cat.affected_product,
                cwe_id=cat.cwe_ids,
                required_action=cat.required_action,
                sources=cat.sources,
            )
            db.add(vuln)
        else:
            if custom_title:
                vuln.title = custom_title
            elif cat.title:
                vuln.title = cat.title
            vuln.description = cat.description or vuln.description
            if cat.cvss_score > 0:
                vuln.cvss_score = cat.cvss_score
            if cat.severity and cat.severity != "UNKNOWN":
                vuln.severity = cat.severity.lower()
            vuln.status = status
            vuln.known_exploited = cat.known_exploited
            vuln.kev_date_added = cat.kev_date_added
            vuln.kev_due_date = cat.kev_due_date
            vuln.known_ransomware_use = cat.known_ransomware_campaign_use
            vuln.affected_product = cat.affected_product
            vuln.cwe_id = cat.cwe_ids
            vuln.required_action = cat.required_action
            vuln.sources = cat.sources

        db.commit()
        db.refresh(vuln)
        return vuln
