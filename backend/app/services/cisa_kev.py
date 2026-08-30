from datetime import UTC, datetime
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OFFLINE_CISA_KEV_FIXTURES: list[dict[str, Any]] = [
    {
        "cveID": "CVE-2024-21762",
        "vendorProject": "Fortinet",
        "product": "FortiOS and FortiProxy",
        "vulnerabilityName": "Fortinet FortiOS and FortiProxy Out-of-Bounds Write Vulnerability",
        "dateAdded": "2024-02-09",
        "shortDescription": "Fortinet FortiOS and FortiProxy contain an out-of-bounds write vulnerability that allows a remote unauthenticated attacker to execute arbitrary code or commands via specially crafted HTTP requests.",
        "requiredAction": "Apply mitigations per vendor instructions or discontinue use of the product if mitigations are unavailable.",
        "dueDate": "2024-02-16",
        "knownRansomwareCampaignUse": "Unknown",
        "notes": "https://www.fortiguard.com/psirt/FG-IR-24-015 ; https://nvd.nist.gov/vuln/detail/CVE-2024-21762",
        "cwes": ["CWE-787"],
    },
    {
        "cveID": "CVE-2023-4966",
        "vendorProject": "Citrix",
        "product": "NetScaler ADC and NetScaler Gateway",
        "vulnerabilityName": "Citrix NetScaler ADC and NetScaler Gateway Information Disclosure Vulnerability (Citrix Bleed)",
        "dateAdded": "2023-10-18",
        "shortDescription": "Citrix NetScaler ADC and NetScaler Gateway contain a buffer overflow vulnerability that allows sensitive information disclosure and session hijacking.",
        "requiredAction": "Apply vendor updates per instructions.",
        "dueDate": "2023-11-08",
        "knownRansomwareCampaignUse": "Known",
        "notes": "https://support.citrix.com/article/CTX579459",
        "cwes": ["CWE-119"],
    },
    {
        "cveID": "CVE-2021-44228",
        "vendorProject": "Apache",
        "product": "Log4j",
        "vulnerabilityName": "Apache Log4j Remote Code Execution Vulnerability (Log4Shell)",
        "dateAdded": "2021-12-10",
        "shortDescription": "Apache Log4j2 contains an untrusted deserialization / JNDI injection vulnerability allowing remote code execution.",
        "requiredAction": "Apply vendor updates or mitigation guidance.",
        "dueDate": "2021-12-24",
        "knownRansomwareCampaignUse": "Known",
        "notes": "https://logging.apache.org/log4j/2.x/security.html",
        "cwes": ["CWE-502"],
    },
    {
        "cveID": "CVE-2024-1709",
        "vendorProject": "ConnectWise",
        "product": "ScreenConnect",
        "vulnerabilityName": "ConnectWise ScreenConnect Authentication Bypass Vulnerability",
        "dateAdded": "2024-02-22",
        "shortDescription": "ConnectWise ScreenConnect contains an authentication bypass vulnerability allowing remote attackers to create admin user accounts.",
        "requiredAction": "Apply updates per vendor instructions.",
        "dueDate": "2024-02-29",
        "knownRansomwareCampaignUse": "Known",
        "notes": "https://www.connectwise.com/company/trust/security-bulletins/connectwise-screenconnect-23.9.8",
        "cwes": ["CWE-288"],
    },
    {
        "cveID": "CVE-2023-38606",
        "vendorProject": "Apple",
        "product": "iOS, iPadOS, and macOS",
        "vulnerabilityName": "Apple Multiple Products State Modification Vulnerability",
        "dateAdded": "2023-07-26",
        "shortDescription": "Apple iOS, iPadOS, and macOS contain a vulnerability allowing malicious apps to modify sensitive kernel state.",
        "requiredAction": "Apply updates per vendor instructions.",
        "dueDate": "2023-08-16",
        "knownRansomwareCampaignUse": "Unknown",
        "notes": "https://support.apple.com/en-us/HT213841",
        "cwes": ["CWE-20"],
    },
]


class CisaKevClient:
    """Client for the CISA Known Exploited Vulnerabilities (KEV) Catalog."""

    def __init__(self, catalog_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.catalog_url = catalog_url or settings.cisa_kev_url
        self.timeout = timeout or settings.http_timeout_seconds

    def fetch_catalog(self) -> list[dict[str, Any]]:
        """Fetch the full CISA KEV catalog feed or fallback to local fixtures if unreachable."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.catalog_url, headers={"Accept": "application/json", "User-Agent": "CYBERVAL-Platform/0.1.0"})
                if response.status_code == 200:
                    data = response.json()
                    return self.parse_catalog(data)
                logger.warning("CISA KEV catalog request returned status %s; falling back to fixture", response.status_code)
        except Exception as exc:
            logger.warning("Failed to fetch live CISA KEV catalog: %s; falling back to offline fixtures", exc)

        return self.parse_catalog({"vulnerabilities": OFFLINE_CISA_KEV_FIXTURES})

    def parse_catalog(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse raw CISA KEV JSON payload into normalized internal records."""
        items = data.get("vulnerabilities", [])
        parsed_records: list[dict[str, Any]] = []

        for item in items:
            cve_id = item.get("cveID", "").strip().upper()
            if not cve_id:
                continue

            date_added_str = item.get("dateAdded")
            date_added = None
            if date_added_str:
                try:
                    date_added = datetime.strptime(date_added_str, "%Y-%m-%d").replace(tzinfo=UTC)
                except ValueError:
                    pass

            due_date_str = item.get("dueDate")
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d").replace(tzinfo=UTC)
                except ValueError:
                    pass

            ransomware = str(item.get("knownRansomwareCampaignUse", "")).strip().lower() == "known"
            cwes = item.get("cwes", [])
            cwe_str = ", ".join(cwes) if isinstance(cwes, list) else str(cwes)

            parsed_records.append({
                "cve_id": cve_id,
                "vendor_project": item.get("vendorProject"),
                "product": item.get("product"),
                "vulnerability_name": item.get("vulnerabilityName", ""),
                "date_added": date_added,
                "due_date": due_date,
                "short_description": item.get("shortDescription", ""),
                "required_action": item.get("requiredAction", ""),
                "known_ransomware_campaign_use": ransomware,
                "notes": item.get("notes", ""),
                "cwe_ids": cwe_str or None,
                "raw_item": item,
            })

        return parsed_records
