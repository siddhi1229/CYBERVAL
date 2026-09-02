"""
P1 Telemetry Service.
Provides standard lookup and telemetry queries for P1 data sources:
Assets, Vulnerabilities, IAM, SIEM, EDR, CSPM, and Threat Intelligence.
"""

from typing import List, Dict, Optional
from .models import (
    Asset,
    AssetCriticality,
    Vulnerability,
    IAMAccount,
    SIEMAlert,
    EDRTelemetry,
    CSPMFinding,
    ThreatIntelIndicator,
)


class P1TelemetryService:
    """
    Upstream P1 Telemetry Service providing deterministic asset inventory,
    vulnerability management data, IAM security posture, SIEM alerts, EDR telemetry,
    CSPM configuration findings, and threat intelligence.
    """

    def __init__(self):
        self._assets: Dict[str, Asset] = {}
        self._vulnerabilities: Dict[str, Vulnerability] = {}
        self._iam_accounts: Dict[str, IAMAccount] = {}
        self._siem_alerts: List[SIEMAlert] = []
        self._edr_telemetry: List[EDRTelemetry] = []
        self._cspm_findings: List[CSPMFinding] = []
        self._threat_intel: List[ThreatIntelIndicator] = []
        self._seed_default_data()

    def _seed_default_data(self):
        # 1. Assets
        assets = [
            Asset(
                id="asset-pay-01",
                name="Payment API",
                asset_type="API Gateway & Microservice",
                criticality=AssetCriticality.TIER_1,
                business_service="Payment Processing",
                internet_exposed=True,
                ip_address="198.51.100.42",
                cloud_provider="AWS",
                tags={"env": "prod", "compliance": "PCI-DSS", "tier": "1"},
                owner="Payments Engineering",
            ),
            Asset(
                id="asset-portal-02",
                name="Customer Portal",
                asset_type="Web Application",
                criticality=AssetCriticality.TIER_2,
                business_service="Customer Banking Web",
                internet_exposed=True,
                ip_address="198.51.100.85",
                cloud_provider="AWS",
                tags={"env": "prod", "compliance": "SOC2", "tier": "2"},
                owner="Frontend Core Team",
            ),
            Asset(
                id="asset-db-03",
                name="Payment Primary Database",
                asset_type="Relational Database (PostgreSQL RDS)",
                criticality=AssetCriticality.TIER_1,
                business_service="Payment Processing",
                internet_exposed=False,
                ip_address="10.0.3.15",
                cloud_provider="AWS",
                tags={"env": "prod", "data_class": "Cardholder Data / PII", "tier": "1"},
                owner="Database Operations",
            ),
            Asset(
                id="asset-auth-04",
                name="Internal Auth Service",
                asset_type="OAuth2 / OIDC Identity Provider",
                criticality=AssetCriticality.TIER_1,
                business_service="Identity & Access Management",
                internet_exposed=False,
                ip_address="10.0.2.8",
                cloud_provider="AWS",
                tags={"env": "prod", "tier": "1"},
                owner="Security Infrastructure",
            ),
            Asset(
                id="asset-analytics-05",
                name="Analytics & BI Pipeline",
                asset_type="Data Lake Worker",
                criticality=AssetCriticality.TIER_3,
                business_service="Corporate Reporting",
                internet_exposed=False,
                ip_address="10.0.8.99",
                cloud_provider="GCP",
                tags={"env": "prod", "tier": "3"},
                owner="Data Analytics",
            ),
        ]
        for a in assets:
            self._assets[a.id] = a

        # 2. Vulnerabilities
        vulnerabilities = [
            Vulnerability(
                cve_id="CVE-2024-21413",
                title="Critical Remote Code Execution in Payment Gateway Handler",
                cvss_score=9.8,
                epss_score=0.892,
                known_exploited=True,
                affected_asset_id="asset-pay-01",
                discovery_date="2026-07-15",
                age_days=45,
                remediation_sla_days=14,
                patch_available=True,
                description="Unchecked deserialization vulnerability allowing remote pre-auth code execution.",
                attack_vector="NETWORK",
            ),
            Vulnerability(
                cve_id="CVE-2023-4863",
                title="Heap Buffer Overflow in Web Rendering Module",
                cvss_score=8.8,
                epss_score=0.741,
                known_exploited=True,
                affected_asset_id="asset-portal-02",
                discovery_date="2026-07-28",
                age_days=32,
                remediation_sla_days=30,
                patch_available=True,
                description="Buffer overflow allowing memory corruption and arbitrary code execution.",
                attack_vector="NETWORK",
            ),
            Vulnerability(
                cve_id="CVE-2023-34362",
                title="SQL Injection in Legacy Analytics ETL Service",
                cvss_score=7.5,
                epss_score=0.312,
                known_exploited=False,
                affected_asset_id="asset-analytics-05",
                discovery_date="2026-08-10",
                age_days=19,
                remediation_sla_days=60,
                patch_available=True,
                description="SQL parameterization defect in backend ingestion worker.",
                attack_vector="NETWORK",
            ),
        ]
        for v in vulnerabilities:
            self._vulnerabilities[v.cve_id] = v

        # 3. IAM Accounts (Multi-privileged accounts with and without MFA)
        iam_accounts = [
            IAMAccount(
                account_id="iam-pay-adm-01",
                username="admin_svc_pay",
                role="Payment_Service_Admin",
                is_privileged=True,
                mfa_enabled=False,
                assigned_assets=["asset-pay-01", "asset-db-03"],
                last_login="2026-08-28T14:22:00Z",
            ),
            IAMAccount(
                account_id="iam-sec-ops-02",
                username="sec_operator_tier1",
                role="Security_Operator",
                is_privileged=True,
                mfa_enabled=False,
                assigned_assets=["asset-auth-04", "asset-pay-01"],
                last_login="2026-08-27T09:15:00Z",
            ),
            IAMAccount(
                account_id="iam-dba-lead-03",
                username="db_admin_root",
                role="Database_Administrator",
                is_privileged=True,
                mfa_enabled=False,
                assigned_assets=["asset-db-03"],
                last_login="2026-08-26T18:00:00Z",
            ),
            IAMAccount(
                account_id="iam-dev-portal-04",
                username="portal_developer",
                role="Web_Developer",
                is_privileged=False,
                mfa_enabled=True,
                assigned_assets=["asset-portal-02"],
                last_login="2026-08-28T16:30:00Z",
            ),
            IAMAccount(
                account_id="iam-infra-lead-05",
                username="infra_lead",
                role="Cloud_Architect",
                is_privileged=True,
                mfa_enabled=True,
                assigned_assets=["asset-pay-01", "asset-portal-02", "asset-auth-04"],
                last_login="2026-08-28T11:00:00Z",
            ),
        ]
        for acc in iam_accounts:
            self._iam_accounts[acc.account_id] = acc

        # 4. SIEM Alerts
        self._siem_alerts = [
            SIEMAlert(
                alert_id="siem-alt-9921",
                asset_id="asset-pay-01",
                alert_type="Brute Force / High-Volume Auth Anomaly",
                severity="HIGH",
                timestamp="2026-08-28T18:45:10Z",
                description="Over 1,420 rapid failed authentication requests targeting /v2/transact endpoints.",
                source_ip="45.154.255.89",
                event_count=1420,
            ),
            SIEMAlert(
                alert_id="siem-alt-9934",
                asset_id="asset-portal-02",
                alert_type="Web App Vulnerability Probe",
                severity="MEDIUM",
                timestamp="2026-08-28T12:10:00Z",
                description="Repeated automated fuzzing payloads observed against customer session headers.",
                source_ip="185.220.101.5",
                event_count=312,
            ),
        ]

        # 5. EDR Telemetry
        self._edr_telemetry = [
            EDRTelemetry(
                telemetry_id="edr-tel-4011",
                asset_id="asset-pay-01",
                detection_type="Credential Dumping (LSASS Memory Read)",
                severity="CRITICAL",
                process_name="powershell.exe",
                command_line="powershell -ep bypass -c Rundll32.exe comsvcs.dll, MiniDump (Get-Process lsass).Id mem.dmp full",
                timestamp="2026-08-28T19:05:00Z",
                mitre_technique="T1003.001",
            ),
            EDRTelemetry(
                telemetry_id="edr-tel-4025",
                asset_id="asset-portal-02",
                detection_type="Suspicious Child Process Spawned",
                severity="MEDIUM",
                process_name="cmd.exe",
                command_line="cmd.exe /c whoami /all",
                timestamp="2026-08-27T22:15:30Z",
                mitre_technique="T1059.003",
            ),
        ]

        # 6. CSPM Findings
        self._cspm_findings = [
            CSPMFinding(
                finding_id="cspm-find-101",
                asset_id="asset-pay-01",
                resource_type="AWS::EC2::SecurityGroup",
                issue="Open Security Group: Inbound rule allows 0.0.0.0/0 on sensitive port 8443",
                severity="CRITICAL",
                compliance_framework="PCI-DSS v4.0 Req 1.3 / CIS AWS 5.2",
                remediation_guide="Restrict security group ingress to internal Application Load Balancer CIDRs.",
            ),
            CSPMFinding(
                finding_id="cspm-find-102",
                asset_id="asset-portal-02",
                resource_type="AWS::S3::Bucket",
                issue="S3 bucket public read permissions enabled on static asset store",
                severity="MEDIUM",
                compliance_framework="CIS AWS 2.1.1",
                remediation_guide="Enable S3 Block Public Access at bucket level.",
            ),
        ]

        # 7. Threat Intelligence
        self._threat_intel = [
            ThreatIntelIndicator(
                indicator_id="ti-ind-8801",
                cve_id="CVE-2024-21413",
                threat_actor="FIN7 / TA505 Financial Threat Group",
                campaign="Operation ShadowVault (Q3 2026)",
                active_in_wild=True,
                targeted_sectors=["Financial Services", "Retail Banking", "Payment Processors"],
                ransomware_associated=True,
                reported_date="2026-08-01",
            ),
            ThreatIntelIndicator(
                indicator_id="ti-ind-8802",
                cve_id="CVE-2023-4863",
                threat_actor="Automated Exploit Kits / Broker",
                campaign="Commodity Web Exploitation",
                active_in_wild=True,
                targeted_sectors=["Broad Commerce"],
                ransomware_associated=False,
                reported_date="2026-07-20",
            ),
        ]

    # Query APIs
    def get_all_assets(self) -> List[Asset]:
        return list(self._assets.values())

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        return self._assets.get(asset_id)

    def get_asset_by_name(self, name: str) -> Optional[Asset]:
        name_lower = name.lower()
        for a in self._assets.values():
            if a.name.lower() == name_lower or name_lower in a.name.lower():
                return a
        return None

    def get_all_vulnerabilities(self) -> List[Vulnerability]:
        return list(self._vulnerabilities.values())

    def get_vulnerability(self, cve_id: str) -> Optional[Vulnerability]:
        return self._vulnerabilities.get(cve_id.upper())

    def get_vulnerabilities_for_asset(self, asset_id: str) -> List[Vulnerability]:
        return [v for v in self._vulnerabilities.values() if v.affected_asset_id == asset_id]

    def get_all_iam_accounts(self) -> List[IAMAccount]:
        return list(self._iam_accounts.values())

    def get_privileged_accounts_without_mfa(self) -> List[IAMAccount]:
        return [
            acc
            for acc in self._iam_accounts.values()
            if acc.is_privileged and not acc.mfa_enabled
        ]

    def get_siem_alerts_for_asset(self, asset_id: str) -> List[SIEMAlert]:
        return [alert for alert in self._siem_alerts if alert.asset_id == asset_id]

    def get_edr_telemetry_for_asset(self, asset_id: str) -> List[EDRTelemetry]:
        return [edr for edr in self._edr_telemetry if edr.asset_id == asset_id]

    def get_cspm_findings_for_asset(self, asset_id: str) -> List[CSPMFinding]:
        return [cspm for cspm in self._cspm_findings if cspm.asset_id == asset_id]

    def get_threat_intel_for_cve(self, cve_id: str) -> List[ThreatIntelIndicator]:
        return [ti for ti in self._threat_intel if ti.cve_id == cve_id]

    def get_all_siem_alerts(self) -> List[SIEMAlert]:
        return list(self._siem_alerts)

    def get_all_edr_telemetry(self) -> List[EDRTelemetry]:
        return list(self._edr_telemetry)

    def get_all_cspm_findings(self) -> List[CSPMFinding]:
        return list(self._cspm_findings)

    def get_all_threat_intel(self) -> List[ThreatIntelIndicator]:
        return list(self._threat_intel)
