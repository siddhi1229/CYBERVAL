import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy.orm import Session

from app.adapters import (
    AssetInventoryAdapter,
    CSPMAdapter,
    EDRAdapter,
    IAMAdapter,
    SIEMAdapter,
)
from app.database import Base, SessionLocal, engine
from app.models import (
    Asset,
    BusinessService,
    Control,
    CveCatalogRecord,
    FrameworkControl,
    Investment,
    Risk,
    Threat,
    Vulnerability,
)


def seed(db: Session, asset_count: int = 100, user_count: int = 35, siem_count: int = 120, edr_count: int = 60, cspm_count: int = 35) -> None:
    if db.query(CveCatalogRecord).first():
        return

    # 1. Master CVE Intelligence Catalog (NVD + CISA KEV Correlated)
    cve_catalog_items = [
        CveCatalogRecord(
            cve_id="CVE-2024-21762",
            title="Fortinet FortiOS Out-of-Bounds Write Vulnerability",
            description="An out-of-bounds write vulnerability in Fortinet FortiOS allows a remote unauthenticated attacker to execute arbitrary code or commands via specially crafted HTTP requests.",
            cvss_score=Decimal("9.8"),
            severity="CRITICAL",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
            known_exploited=True,
            kev_date_added=datetime(2024, 2, 9, tzinfo=UTC),
            kev_due_date=datetime(2024, 2, 16, tzinfo=UTC),
            known_ransomware_campaign_use=False,
            affected_vendor="Fortinet",
            affected_product="FortiOS, FortiProxy",
            cwe_ids="CWE-787",
            required_action="Apply mitigations per vendor instructions or discontinue use of the product if mitigations are unavailable.",
            sources="NVD,CISA_KEV",
        ),
        CveCatalogRecord(
            cve_id="CVE-2024-3094",
            title="XZ Utils Malicious Code Execution Backdoor",
            description="Malicious code in upstream xz-utils tarballs impacts liblzma in SSH daemon authentication routines, enabling remote unauthorized authentication bypass.",
            cvss_score=Decimal("10.0"),
            severity="CRITICAL",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            known_exploited=False,
            affected_vendor="Tukaani",
            affected_product="XZ Utils, liblzma",
            cwe_ids="CWE-506",
            required_action="Downgrade xz-utils to uncompromised versions (5.4.x) immediately.",
            sources="NVD",
        ),
        CveCatalogRecord(
            cve_id="CVE-2023-4966",
            title="Citrix NetScaler ADC / Gateway Information Disclosure (Citrix Bleed)",
            description="Sensitive information disclosure in NetScaler ADC and Gateway allows unauthenticated attackers to extract session cookies and bypass multifactor authentication.",
            cvss_score=Decimal("9.4"),
            severity="CRITICAL",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
            known_exploited=True,
            kev_date_added=datetime(2023, 10, 18, tzinfo=UTC),
            kev_due_date=datetime(2023, 11, 8, tzinfo=UTC),
            known_ransomware_campaign_use=True,
            affected_vendor="Citrix",
            affected_product="NetScaler ADC, NetScaler Gateway",
            cwe_ids="CWE-119",
            required_action="Apply vendor patches and terminate all active user sessions.",
            sources="NVD,CISA_KEV",
        ),
        CveCatalogRecord(
            cve_id="CVE-2021-44228",
            title="Apache Log4j2 JNDI Remote Code Execution (Log4Shell)",
            description="Apache Log4j2 JNDI features do not protect against attacker-controlled LDAP endpoints, allowing remote code execution via log message formatting.",
            cvss_score=Decimal("10.0"),
            severity="CRITICAL",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            known_exploited=True,
            kev_date_added=datetime(2021, 12, 10, tzinfo=UTC),
            kev_due_date=datetime(2021, 12, 24, tzinfo=UTC),
            known_ransomware_campaign_use=True,
            affected_vendor="Apache",
            affected_product="Log4j",
            cwe_ids="CWE-502, CWE-400",
            required_action="Upgrade to Log4j 2.15.0+ or apply log4j2.formatMsgNoLookups mitigation.",
            sources="NVD,CISA_KEV",
        ),
        CveCatalogRecord(
            cve_id="CVE-2024-1709",
            title="ConnectWise ScreenConnect Authentication Bypass Vulnerability",
            description="ConnectWise ScreenConnect contains an authentication bypass vulnerability allowing remote attackers to create admin accounts.",
            cvss_score=Decimal("10.0"),
            severity="CRITICAL",
            cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            known_exploited=True,
            kev_date_added=datetime(2024, 2, 22, tzinfo=UTC),
            kev_due_date=datetime(2024, 2, 29, tzinfo=UTC),
            known_ransomware_campaign_use=True,
            affected_vendor="ConnectWise",
            affected_product="ScreenConnect",
            cwe_ids="CWE-288",
            required_action="Apply the vendor update to version 23.9.8 or higher immediately.",
            sources="NVD,CISA_KEV",
        ),
    ]
    db.add_all(cve_catalog_items)
    db.flush()

    # 2. Business Services (5 services)
    payment = BusinessService(
        name="Payment Service",
        owner="Digital Commerce",
        criticality="critical",
        annual_revenue=Decimal("480000000"),
    )
    customer = BusinessService(
        name="Customer Data Platform",
        owner="Data Office",
        criticality="high",
        annual_revenue=Decimal("260000000"),
    )
    banking = BusinessService(
        name="Core Banking & Settlement",
        owner="Banking Operations",
        criticality="critical",
        annual_revenue=Decimal("850000000"),
    )
    identity = BusinessService(
        name="Digital Identity & Authentication",
        owner="SecOps & IAM",
        criticality="critical",
        annual_revenue=Decimal("320000000"),
    )
    analytics = BusinessService(
        name="Analytics & Business Intelligence",
        owner="Data Office",
        criticality="medium",
        annual_revenue=Decimal("110000000"),
    )
    db.add_all([payment, customer, banking, identity, analytics])
    db.flush()

    # 3. Foundational Anchor Assets (Preserving original P1 contracts)
    assets = [
        Asset(
            asset_id_code="GATEWAY-01",
            name="Internet Gateway",
            asset_type="network",
            owner="Platform",
            department="Infrastructure",
            criticality="CRITICAL",
            business_value=Decimal("18000000.00"),
            internet_exposed=True,
            hostname="gw-edge-01.cyberval.net",
            ip_address="198.51.100.1",
            cloud_provider="on-premise",
            status="active",
            business_service=payment,
        ),
        Asset(
            asset_id_code="PAYMENT-API-01",
            name="Payment API",
            asset_type="application",
            owner="Payments",
            department="Engineering",
            criticality="CRITICAL",
            business_value=Decimal("48000000.00"),
            internet_exposed=True,
            hostname="api-pay-prod-01.cyberval.net",
            ip_address="10.0.1.50",
            cloud_provider="AWS",
            status="active",
            business_service=payment,
        ),
        Asset(
            asset_id_code="CUSTOMER-DB-01",
            name="Customer Database",
            asset_type="database",
            owner="Data Office",
            department="Data",
            criticality="HIGH",
            business_value=Decimal("26000000.00"),
            internet_exposed=False,
            hostname="db-cust-primary.internal",
            ip_address="10.0.2.10",
            cloud_provider="AWS",
            status="active",
            business_service=customer,
        ),
    ]
    db.add_all(assets)
    db.flush()

    # 4. Normalized & Correlated Asset Vulnerabilities
    vulnerabilities = [
        Vulnerability(
            cve_id="CVE-2024-21762",
            title="Fortinet FortiOS Out-of-Bounds Write Vulnerability",
            description="Perimeter appliance remote code execution via malformed HTTP requests.",
            cvss_score=Decimal("9.8"),
            severity="critical",
            status="open",
            known_exploited=True,
            kev_date_added=datetime(2024, 2, 9, tzinfo=UTC),
            kev_due_date=datetime(2024, 2, 16, tzinfo=UTC),
            known_ransomware_use=False,
            affected_product="FortiOS, FortiProxy",
            cwe_id="CWE-787",
            required_action="Apply mitigations per vendor instructions immediately.",
            sources="NVD,CISA_KEV",
            asset=assets[0],
        ),
        Vulnerability(
            cve_id="CVE-2023-4966",
            title="Citrix NetScaler ADC / Gateway Information Disclosure (Citrix Bleed)",
            description="Session token disclosure leading to MFA bypass on gateway appliances.",
            cvss_score=Decimal("9.4"),
            severity="critical",
            status="open",
            known_exploited=True,
            kev_date_added=datetime(2023, 10, 18, tzinfo=UTC),
            kev_due_date=datetime(2023, 11, 8, tzinfo=UTC),
            known_ransomware_use=True,
            affected_product="NetScaler Gateway",
            cwe_id="CWE-119",
            required_action="Patch appliance and terminate all active sessions.",
            sources="NVD,CISA_KEV",
            asset=assets[0],
        ),
        Vulnerability(
            cve_id="CVE-2024-3094",
            title="XZ Utils Malicious Code Execution Backdoor",
            description="Supply-chain compromise in liblzma affecting SSH authentication routines.",
            cvss_score=Decimal("10.0"),
            severity="critical",
            status="open",
            known_exploited=False,
            affected_product="XZ Utils, liblzma",
            cwe_id="CWE-506",
            required_action="Downgrade to clean xz-utils package.",
            sources="NVD",
            asset=assets[1],
        ),
        Vulnerability(
            cve_id="CVE-2021-44228",
            title="Apache Log4j2 JNDI Remote Code Execution (Log4Shell)",
            description="Remote code execution via attacker-controlled LDAP JNDI lookups in logging.",
            cvss_score=Decimal("10.0"),
            severity="critical",
            status="open",
            known_exploited=True,
            kev_date_added=datetime(2021, 12, 10, tzinfo=UTC),
            kev_due_date=datetime(2021, 12, 24, tzinfo=UTC),
            known_ransomware_use=True,
            affected_product="Log4j",
            cwe_id="CWE-502",
            required_action="Upgrade to patched Log4j library.",
            sources="NVD,CISA_KEV",
            asset=assets[1],
        ),
    ]
    db.add_all(vulnerabilities)
    db.flush()

    # 5. Expand Enterprise Assets Inventory (up to configured count, default: 100)
    asset_adapter = AssetInventoryAdapter()
    asset_adapter.ingest(db, count=asset_count)

    # 6. Seed Enterprise IAM Users & Asset Access Permissions (default: 35)
    iam_adapter = IAMAdapter()
    iam_adapter.ingest(db, count=user_count)

    # 7. Seed SIEM Security Event Telemetry (default: 120)
    siem_adapter = SIEMAdapter()
    siem_adapter.ingest(db, count=siem_count)

    # 8. Seed EDR Endpoint Telemetry (default: 60)
    edr_adapter = EDRAdapter()
    edr_adapter.ingest(db, count=edr_count)

    # 9. Seed CSPM Cloud Security Posture Findings (default: 35)
    cspm_adapter = CSPMAdapter()
    cspm_adapter.ingest(db, count=cspm_count)

    # 10. Threats (5 Threats)
    threats = [
        Threat(
            name="Ransomware",
            category="malware",
            annual_frequency=Decimal("0.18"),
            source="synthetic threat intelligence",
        ),
        Threat(
            name="Credential Theft",
            category="identity",
            annual_frequency=Decimal("0.32"),
            source="synthetic threat intelligence",
        ),
        Threat(
            name="Remote Code Execution (RCE)",
            category="exploit",
            annual_frequency=Decimal("0.25"),
            source="synthetic threat intelligence",
        ),
        Threat(
            name="Supply Chain Compromise",
            category="third_party",
            annual_frequency=Decimal("0.12"),
            source="synthetic threat intelligence",
        ),
        Threat(
            name="Cloud Misconfiguration Exploitation",
            category="cloud",
            annual_frequency=Decimal("0.28"),
            source="synthetic threat intelligence",
        ),
    ]
    db.add_all(threats)

    # 11. Controls (8 Master Controls)
    controls = [
        Control(
            name="Multi-factor Authentication",
            description="Require phishing-resistant MFA for privileged access.",
            effectiveness=Decimal("0.72"),
            status="active",
        ),
        Control(
            name="Critical Vulnerability Patching",
            description="Patch exploitable critical vulnerabilities within defined SLA.",
            effectiveness=Decimal("0.68"),
            status="active",
        ),
        Control(
            name="Network Segmentation",
            description="Restrict movement between internet-facing and sensitive services.",
            effectiveness=Decimal("0.61"),
            status="active",
        ),
        Control(
            name="Web Application Firewall (WAF)",
            description="Inspect and filter inbound HTTP/HTTPS traffic to prevent exploit payloads.",
            effectiveness=Decimal("0.85"),
            status="active",
        ),
        Control(
            name="Endpoint Detection & Response (EDR)",
            description="Continuous endpoint behavioral monitoring, memory protection, and threat isolation.",
            effectiveness=Decimal("0.80"),
            status="active",
        ),
        Control(
            name="Least Privilege Access Control",
            description="Strict role-based and attribute-based access limiting administrative lateral pivot.",
            effectiveness=Decimal("0.75"),
            status="active",
        ),
        Control(
            name="Database Encryption at Rest & In Transit",
            description="AES-256 cryptographic protection for core transactional databases.",
            effectiveness=Decimal("0.88"),
            status="active",
        ),
        Control(
            name="Cloud Security Posture Monitoring (CSPM)",
            description="Continuous scanning of cloud security groups, IAM policies, and infrastructure misconfigurations.",
            effectiveness=Decimal("0.70"),
            status="active",
        ),
    ]
    db.add_all(controls)
    db.flush()

    # 12. Financial Risks
    risks = [
        Risk(
            asset=assets[0],
            likelihood=Decimal("0.24"),
            financial_impact=Decimal("18000000"),
            expected_annual_loss=Decimal("4320000"),
            confidence=Decimal("0.82"),
        ),
        Risk(
            asset=assets[1],
            likelihood=Decimal("0.19"),
            financial_impact=Decimal("47000000"),
            expected_annual_loss=Decimal("8930000"),
            confidence=Decimal("0.79"),
        ),
        Risk(
            asset=assets[2],
            likelihood=Decimal("0.11"),
            financial_impact=Decimal("31000000"),
            expected_annual_loss=Decimal("3410000"),
            confidence=Decimal("0.76"),
        ),
    ]
    db.add_all(risks)

    # 13. Investments
    investments = [
        Investment(
            name="Privileged Access MFA",
            description="Extend phishing-resistant MFA to privileged paths.",
            cost=Decimal("2500000"),
            risk_reduction=Decimal("4200000"),
            implementation_days=45,
        ),
        Investment(
            name="Critical Patching Sprint",
            description="Remediate internet-facing critical vulnerabilities.",
            cost=Decimal("1500000"),
            risk_reduction=Decimal("5100000"),
            implementation_days=30,
        ),
        Investment(
            name="Service Segmentation",
            description="Segment payment and data service trust zones.",
            cost=Decimal("4000000"),
            risk_reduction=Decimal("3600000"),
            implementation_days=60,
        ),
        Investment(
            name="Advanced EDR Memory Protection",
            description="Deploy anti-mimikatz and LSASS credential protection on all servers.",
            cost=Decimal("3000000"),
            risk_reduction=Decimal("9000000"),
            implementation_days=21,
        ),
    ]
    db.add_all(investments)

    # 14. Framework Mappings
    for framework in ["NIST CSF", "ISO/IEC 27001", "CIS Controls", "RBI CSF", "SEBI CSCRF"]:
        for control in controls:
            db.add(
                FrameworkControl(
                    framework=framework,
                    control_code=f"{framework[:3].upper()}-{control.id}",
                    control_name=control.name,
                    master_control_id=control.id,
                )
            )
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed(session)
    print("Synthetic CYBERVAL seed data loaded with multi-source security data & NVD + CISA KEV intelligence")
