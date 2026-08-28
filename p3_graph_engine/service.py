"""
P3 Attack Path & Graph Engine Service.
Provides graph traversal, attack path analysis, dependency mapping,
and choke point identification for critical business services.
"""

from typing import List, Dict, Any, Optional
from .models import (
    GraphNode,
    GraphEdge,
    AttackPath,
    AttackPathStep,
    BusinessService,
)


class P3GraphEngineService:
    """
    Upstream P3 Graph & Attack Path Service.
    Maps relationships between threats, assets, credentials, vulnerabilities, and business services.
    """

    def __init__(self):
        self._seed_graph_data()

    def _seed_graph_data(self):
        # 1. Business Services
        self._business_services: Dict[str, BusinessService] = {
            "srv-pay": BusinessService(
                service_id="srv-pay",
                name="Payment Processing",
                tier="Tier 1 - Mission Critical",
                description="Core payment authorization, card processing, and settlement engine.",
                dependent_asset_ids=["asset-pay-01", "asset-db-03", "asset-auth-04"],
                maximum_tolerable_downtime_hours=1,
                financial_loss_per_hour_downtime=250000.0,
            ),
            "srv-portal": BusinessService(
                service_id="srv-portal",
                name="Customer Banking Web",
                tier="Tier 2 - Business Critical",
                description="Online retail customer portal for accounts and transfers.",
                dependent_asset_ids=["asset-portal-02", "asset-auth-04"],
                maximum_tolerable_downtime_hours=4,
                financial_loss_per_hour_downtime=75000.0,
            ),
            "srv-analytics": BusinessService(
                service_id="srv-analytics",
                name="Corporate Reporting & BI",
                tier="Tier 3 - Operational",
                description="Internal reporting, business intelligence, and compliance metrics.",
                dependent_asset_ids=["asset-analytics-05"],
                maximum_tolerable_downtime_hours=24,
                financial_loss_per_hour_downtime=10000.0,
            ),
        }

        # 2. Attack Paths
        self._attack_paths: List[AttackPath] = [
            AttackPath(
                path_id="AP-PAY-001",
                name="External RCE -> Credential Dump -> Lateral Movement to Payment DB",
                source_threat="Internet-Based Threat Actor (FIN7 / ShadowVault)",
                target_business_service="Payment Processing",
                target_critical_asset="Payment Primary Database (asset-db-03)",
                traversal_probability=0.68,
                estimated_financial_loss=3950000.0,
                steps=[
                    AttackPathStep(
                        step_number=1,
                        from_entity="External Internet (0.0.0.0/0)",
                        to_entity="Payment API (asset-pay-01)",
                        action_type="EXPLOIT_VULNERABILITY",
                        technique_id="T1190 - Exploit Public-Facing Application",
                        description="Exploits CVE-2024-21413 via unrestricted port 8443 ingress.",
                        choke_point=True,
                        remediation_control="CTRL-VULN-02 / CTRL-NET-03",
                    ),
                    AttackPathStep(
                        step_number=2,
                        from_entity="Payment API (asset-pay-01)",
                        to_entity="IAM Account: admin_svc_pay",
                        action_type="CREDENTIAL_ABUSE",
                        technique_id="T1003.001 - LSASS Memory Dumping",
                        description="Dumps memory on host to extract un-MFA'd privileged service credentials.",
                        choke_point=True,
                        remediation_control="CTRL-IAM-01 (MFA Enforcement)",
                    ),
                    AttackPathStep(
                        step_number=3,
                        from_entity="IAM Account: admin_svc_pay",
                        to_entity="Payment Primary Database (asset-db-03)",
                        action_type="LATERAL_MOVEMENT",
                        technique_id="T1021.002 - SMB/Remote Admin lateral pivot",
                        description="Pivots across internal network to database using stolen admin credentials.",
                        choke_point=True,
                        remediation_control="CTRL-NET-03 (Subnet Microsegmentation)",
                    ),
                    AttackPathStep(
                        step_number=4,
                        from_entity="Payment Primary Database (asset-db-03)",
                        to_entity="Business Service: Payment Processing",
                        action_type="DATA_EXFILTRATION",
                        technique_id="T1486 / T1048 - Exfiltration & Data Encryption",
                        description="Exfiltrates cardholder PII and encrypts database storage, halting payments.",
                        choke_point=False,
                        remediation_control=None,
                    ),
                ],
                choke_points=[
                    "Step 1: Ingress & CVE Patching (Payment API)",
                    "Step 2: Privileged MFA Enforcement (admin_svc_pay)",
                    "Step 3: Database Network Microsegmentation (Subnet 10.0.3.0/24)",
                ],
                active_threat_indicators=[
                    "SIEM Alert: 1,420 brute-force / auth requests on Payment API",
                    "EDR Telemetry: LSASS credential dump detected on Payment API",
                    "CSPM Finding: Open SG 0.0.0.0/0:8443 on Payment API",
                    "Threat Intel: Active FIN7 campaign targeting CVE-2024-21413",
                ],
            ),
            AttackPath(
                path_id="AP-PORTAL-002",
                name="Customer Portal Buffer Overflow -> S3 Bucket Data Exposure",
                source_threat="Automated Web Exploit Kits",
                target_business_service="Customer Banking Web",
                target_critical_asset="Customer Portal (asset-portal-02)",
                traversal_probability=0.42,
                estimated_financial_loss=2263158.0,
                steps=[
                    AttackPathStep(
                        step_number=1,
                        from_entity="External Internet",
                        to_entity="Customer Portal (asset-portal-02)",
                        action_type="EXPLOIT_VULNERABILITY",
                        technique_id="T1190 - Exploit Public-Facing Application",
                        description="Exploits CVE-2023-4863 heap buffer overflow in web rendering.",
                        choke_point=True,
                        remediation_control="CTRL-VULN-02",
                    ),
                    AttackPathStep(
                        step_number=2,
                        from_entity="Customer Portal (asset-portal-02)",
                        to_entity="AWS S3 Customer Storage",
                        action_type="DATA_EXFILTRATION",
                        technique_id="T1530 - Cloud Storage Object Access",
                        description="Accesses unauthenticated public S3 bucket containing customer receipts.",
                        choke_point=True,
                        remediation_control="CTRL-CSPM-02 (S3 Block Public Access)",
                    ),
                ],
                choke_points=[
                    "Step 1: Patch CVE-2023-4863 on Customer Portal",
                    "Step 2: Enable S3 Block Public Access",
                ],
                active_threat_indicators=[
                    "SIEM Alert: Automated fuzzing payloads on Customer Portal",
                    "CSPM Finding: Public read permissions on S3 bucket",
                ],
            ),
        ]

    def get_all_attack_paths(self) -> List[AttackPath]:
        return list(self._attack_paths)

    def get_attack_paths_for_asset(self, asset_id_or_name: str) -> List[AttackPath]:
        query = asset_id_or_name.lower()
        matched = []
        for path in self._attack_paths:
            if query in path.target_critical_asset.lower() or query in path.name.lower():
                matched.append(path)
                continue
            for step in path.steps:
                if query in step.from_entity.lower() or query in step.to_entity.lower():
                    matched.append(path)
                    break
        return matched

    def get_attack_paths_reaching_critical_services(self) -> List[AttackPath]:
        return [p for p in self._attack_paths if p.target_business_service in ["Payment Processing", "Customer Banking Web"]]

    def get_business_service(self, service_id_or_name: str) -> Optional[BusinessService]:
        query = service_id_or_name.lower()
        for s in self._business_services.values():
            if s.service_id.lower() == query or s.name.lower() == query or query in s.name.lower():
                return s
        return None

    def get_all_business_services(self) -> List[BusinessService]:
        return list(self._business_services.values())
