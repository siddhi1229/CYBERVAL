import logging
from decimal import Decimal
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

OFFLINE_NVD_FIXTURES: dict[str, dict[str, Any]] = {
    "CVE-2024-21762": {
        "cve_id": "CVE-2024-21762",
        "title": "Fortinet FortiOS Out-of-Bounds Write Vulnerability",
        "description": "An out-of-bounds write vulnerability in Fortinet FortiOS versions 7.4.0 through 7.4.2, 7.2.0 through 7.2.6, 7.0.0 through 7.0.13, 6.4.0 through 6.4.14, 6.2.0 through 6.2.15, 6.0.0 through 6.0.17 allows a remote unauthenticated attacker to execute arbitrary code or commands via specially crafted HTTP requests.",
        "cvss_score": Decimal("9.8"),
        "severity": "CRITICAL",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        "affected_vendor": "Fortinet",
        "affected_product": "FortiOS, FortiProxy",
        "cwe_ids": "CWE-787",
        "required_action": "Apply mitigations per vendor instructions or discontinue use of the product if mitigations are unavailable.",
    },
    "CVE-2024-3094": {
        "cve_id": "CVE-2024-3094",
        "title": "XZ Utils Malicious Code Execution Backdoor",
        "description": "Malicious code was discovered in upstream tarballs of xz-utils starting with version 5.6.0 through 5.6.1. The backdoor impacts liblzma in SSH daemon authentication routines, enabling remote unauthorized authentication bypass and code execution.",
        "cvss_score": Decimal("10.0"),
        "severity": "CRITICAL",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "affected_vendor": "Tukaani",
        "affected_product": "XZ Utils, liblzma",
        "cwe_ids": "CWE-506",
        "required_action": "Downgrade xz-utils to uncompromised versions (5.4.x) immediately.",
    },
    "CVE-2023-4966": {
        "cve_id": "CVE-2023-4966",
        "title": "Citrix NetScaler ADC / Gateway Information Disclosure (Citrix Bleed)",
        "description": "Sensitive information disclosure in NetScaler ADC and NetScaler Gateway allows an unauthenticated remote attacker to extract session cookies and bypass multifactor authentication.",
        "cvss_score": Decimal("9.4"),
        "severity": "CRITICAL",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
        "affected_vendor": "Citrix",
        "affected_product": "NetScaler ADC, NetScaler Gateway",
        "cwe_ids": "CWE-119",
        "required_action": "Apply vendor patches and terminate all active user sessions.",
    },
    "CVE-2021-44228": {
        "cve_id": "CVE-2021-44228",
        "title": "Apache Log4j2 JNDI Remote Code Execution (Log4Shell)",
        "description": "Apache Log4j2 versions 2.0-beta9 through 2.14.1 JNDI features do not protect against attacker-controlled LDAP and other JNDI related endpoints, allowing remote code execution via log message formatting.",
        "cvss_score": Decimal("10.0"),
        "severity": "CRITICAL",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "affected_vendor": "Apache Software Foundation",
        "affected_product": "Log4j",
        "cwe_ids": "CWE-502, CWE-400",
        "required_action": "Upgrade to Log4j 2.15.0+ or apply log4j2.formatMsgNoLookups mitigation.",
    },
    "CVE-2024-1709": {
        "cve_id": "CVE-2024-1709",
        "title": "ConnectWise ScreenConnect Authentication Bypass Vulnerability",
        "description": "ConnectWise ScreenConnect 23.9.7 and prior contains an authentication bypass using an alternate path or channel vulnerability that allows an attacker with network access to create administrative accounts.",
        "cvss_score": Decimal("10.0"),
        "severity": "CRITICAL",
        "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
        "affected_vendor": "ConnectWise",
        "affected_product": "ScreenConnect",
        "cwe_ids": "CWE-288",
        "required_action": "Apply the vendor update to version 23.9.8 or higher immediately.",
    },
    "CVE-2023-38606": {
        "cve_id": "CVE-2023-38606",
        "title": "Apple WebKit / Kernel State Modification Vulnerability",
        "description": "An app may be able to modify sensitive kernel state. Apple addressed this issue with improved state management for iOS and iPadOS.",
        "cvss_score": Decimal("7.8"),
        "severity": "HIGH",
        "cvss_vector": "CVSS:3.1/AV:L/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:H",
        "affected_vendor": "Apple",
        "affected_product": "iOS, iPadOS, macOS",
        "cwe_ids": "CWE-20",
        "required_action": "Apply Apple security updates.",
    },
}


class NvdClient:
    """Client for NIST National Vulnerability Database (NVD) REST API 2.0."""

    def __init__(self, api_url: str | None = None, api_key: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.api_url = (api_url or settings.nvd_api_url).rstrip("/")
        self.api_key = api_key or settings.nvd_api_key
        self.timeout = timeout or settings.http_timeout_seconds

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "CYBERVAL-Platform/0.1.0",
        }
        if self.api_key:
            headers["apiKey"] = self.api_key
        return headers

    def fetch_cve(self, cve_id: str) -> dict[str, Any] | None:
        """Fetch vulnerability record by CVE ID from NVD API 2.0 with fallback fixture support."""
        cve_id = cve_id.strip().upper()
        url = f"{self.api_url}?cveId={cve_id}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._headers())
                if response.status_code == 200:
                    data = response.json()
                    vulnerabilities = data.get("vulnerabilities", [])
                    if vulnerabilities:
                        return self.parse_nvd_item(vulnerabilities[0])
                elif response.status_code in (403, 429):
                    logger.warning("NVD API rate-limit/auth constraint (%s) for %s; using fixture if available", response.status_code, cve_id)
                else:
                    logger.warning("NVD API returned status %s for %s", response.status_code, cve_id)
        except Exception as exc:
            logger.warning("NVD API request failed for %s: %s; checking offline fixtures", cve_id, exc)

        # Fallback to offline fixture if available
        if cve_id in OFFLINE_NVD_FIXTURES:
            return dict(OFFLINE_NVD_FIXTURES[cve_id])
        return None

    def fetch_cves_batch(self, cve_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch multiple CVEs from NVD."""
        results: list[dict[str, Any]] = []
        for cve_id in cve_ids:
            record = self.fetch_cve(cve_id)
            if record:
                results.append(record)
        return results

    def parse_nvd_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize an NVD 2.0 vulnerability item structure."""
        cve_data = item.get("cve", item)
        cve_id = cve_data.get("id", "").strip().upper()

        # Descriptions
        descriptions = cve_data.get("descriptions", [])
        desc_text = ""
        for desc in descriptions:
            if desc.get("lang") == "en":
                desc_text = desc.get("value", "")
                break
        if not desc_text and descriptions:
            desc_text = descriptions[0].get("value", "")

        # CVSS Score and Severity
        metrics = cve_data.get("metrics", {})
        cvss_score = Decimal("0.0")
        severity = "UNKNOWN"
        cvss_vector = None

        if "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
            metric = metrics["cvssMetricV31"][0]
            data = metric.get("cvssData", {})
            cvss_score = Decimal(str(data.get("baseScore", 0.0)))
            severity = str(data.get("baseSeverity", "UNKNOWN")).upper()
            cvss_vector = data.get("vectorString")
        elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
            metric = metrics["cvssMetricV30"][0]
            data = metric.get("cvssData", {})
            cvss_score = Decimal(str(data.get("baseScore", 0.0)))
            severity = str(data.get("baseSeverity", "UNKNOWN")).upper()
            cvss_vector = data.get("vectorString")
        elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
            metric = metrics["cvssMetricV2"][0]
            data = metric.get("cvssData", {})
            cvss_score = Decimal(str(data.get("baseScore", 0.0)))
            severity = str(metric.get("baseSeverity", "UNKNOWN")).upper()
            cvss_vector = data.get("vectorString")

        # Weaknesses / CWEs
        cwes: list[str] = []
        for weakness in cve_data.get("weaknesses", []):
            for desc in weakness.get("description", []):
                val = desc.get("value")
                if val and val not in cwes:
                    cwes.append(val)
        cwe_str = ", ".join(cwes) if cwes else None

        # Affected software / CPEs extraction
        vendors: set[str] = set()
        products: set[str] = set()
        for config in cve_data.get("configurations", []):
            for node in config.get("nodes", []):
                for match in node.get("cpeMatch", []):
                    cpe = match.get("criteria", "")
                    # Format: cpe:2.3:a:vendor:product:...
                    parts = cpe.split(":")
                    if len(parts) >= 5:
                        vendor = parts[3].replace("_", " ").title()
                        prod = parts[4].replace("_", " ").title()
                        if vendor and vendor != "*":
                            vendors.add(vendor)
                        if prod and prod != "*":
                            products.add(prod)

        affected_vendor = ", ".join(sorted(vendors)) if vendors else None
        affected_product = ", ".join(sorted(products)) if products else None

        # CISA annotations present directly in NVD
        cisa_name = cve_data.get("cisaVulnerabilityName")
        cisa_action = cve_data.get("cisaRequiredAction")

        title = cisa_name or (f"{affected_product} Vulnerability" if affected_product else f"Vulnerability in {cve_id}")

        return {
            "cve_id": cve_id,
            "title": title[:300],
            "description": desc_text or None,
            "cvss_score": cvss_score,
            "severity": severity,
            "cvss_vector": cvss_vector,
            "affected_vendor": affected_vendor,
            "affected_product": affected_product,
            "cwe_ids": cwe_str,
            "required_action": cisa_action,
            "source": "NVD",
            "raw_payload": cve_data,
        }
