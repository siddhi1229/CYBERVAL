import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import (
    Asset, BusinessService, Control, FrameworkControl, Investment, Risk,
    SecurityEvent, Threat, User, Vulnerability,
)


def seed(db: Session) -> None:
    if db.query(Asset).first():
        return

    # 1. Business Services (5 services)
    payment_svc = BusinessService(
        name="Payment Service",
        owner="Digital Commerce",
        criticality="critical",
        annual_revenue=Decimal("480000000"),
    )
    customer_svc = BusinessService(
        name="Customer Data Platform",
        owner="Data Office",
        criticality="high",
        annual_revenue=Decimal("260000000"),
    )
    banking_svc = BusinessService(
        name="Core Banking & Settlement",
        owner="Banking Operations",
        criticality="critical",
        annual_revenue=Decimal("850000000"),
    )
    identity_svc = BusinessService(
        name="Digital Identity & Authentication",
        owner="SecOps & IAM",
        criticality="critical",
        annual_revenue=Decimal("320000000"),
    )
    analytics_svc = BusinessService(
        name="Analytics & Business Intelligence",
        owner="Data Office",
        criticality="medium",
        annual_revenue=Decimal("110000000"),
    )
    services = [payment_svc, customer_svc, banking_svc, identity_svc, analytics_svc]
    db.add_all(services)
    db.flush()

    # 2. Controls (8 Master Controls)
    controls = [
        Control(name="Multi-factor Authentication", description="Require phishing-resistant MFA for privileged access.", effectiveness=Decimal("0.72"), status="active"),
        Control(name="Critical Vulnerability Patching", description="Patch exploitable critical vulnerabilities within defined SLA.", effectiveness=Decimal("0.68"), status="active"),
        Control(name="Network Segmentation", description="Restrict movement between internet-facing and sensitive internal services.", effectiveness=Decimal("0.61"), status="active"),
        Control(name="Web Application Firewall (WAF)", description="Inspect and filter inbound HTTP/HTTPS traffic to prevent exploit payloads.", effectiveness=Decimal("0.85"), status="active"),
        Control(name="Endpoint Detection & Response (EDR)", description="Continuous endpoint behavioral monitoring, memory protection, and threat isolation.", effectiveness=Decimal("0.80"), status="active"),
        Control(name="Least Privilege Access Control", description="Strict role-based and attribute-based access limiting administrative lateral pivot.", effectiveness=Decimal("0.75"), status="active"),
        Control(name="Database Encryption at Rest & In Transit", description="AES-256 cryptographic protection for core transactional databases.", effectiveness=Decimal("0.88"), status="active"),
        Control(name="Cloud Security Posture Monitoring (CSPM)", description="Continuous scanning of cloud security groups, IAM policies, and infrastructure misconfigurations.", effectiveness=Decimal("0.70"), status="active"),
    ]
    db.add_all(controls)
    db.flush()

    # Framework Control Mappings
    for framework in ["NIST CSF", "ISO/IEC 27001", "CIS Controls", "RBI CSF", "SEBI CSCRF"]:
        for control in controls:
            db.add(FrameworkControl(framework=framework, control_code=f"{framework[:3].upper()}-{control.id:02d}", control_name=control.name, master_control_id=control.id))

    # 3. Threats (5 Threat actors / categories)
    threats = [
        Threat(name="Ransomware", category="malware", annual_frequency=Decimal("0.18"), source="synthetic threat intelligence"),
        Threat(name="Credential Theft", category="identity", annual_frequency=Decimal("0.32"), source="synthetic threat intelligence"),
        Threat(name="Remote Code Execution (RCE)", category="exploit", annual_frequency=Decimal("0.25"), source="synthetic threat intelligence"),
        Threat(name="Supply Chain Compromise", category="third_party", annual_frequency=Decimal("0.12"), source="synthetic threat intelligence"),
        Threat(name="Cloud Misconfiguration Exploitation", category="cloud", annual_frequency=Decimal("0.28"), source="synthetic threat intelligence"),
    ]
    db.add_all(threats)
    db.flush()

    # 4. Users (35 Enterprise Users: Admins, DevOps, Engineers, Analysts, Operators)
    user_roles = [
        ("Alice Chen", "alice.chen@cyberval.internal", "Cloud Architect", True),
        ("Bob Smith", "bob.smith@cyberval.internal", "DevOps Admin", True),
        ("Carol Davis", "carol.davis@cyberval.internal", "Payment Service Admin", True),
        ("Dave Wilson", "dave.wilson@cyberval.internal", "Database Administrator", True),
        ("Eve Martinez", "eve.martinez@cyberval.internal", "Lead Security Engineer", True),
        ("Frank Miller", "frank.miller@cyberval.internal", "Site Reliability Engineer", True),
        ("Grace Taylor", "grace.taylor@cyberval.internal", "Identity Administrator", True),
        ("Henry Anderson", "henry.anderson@cyberval.internal", "Platform Engineer", True),
        ("Ivy Thomas", "ivy.thomas@cyberval.internal", "Infrastructure Lead", True),
        ("Jack Jackson", "jack.jackson@cyberval.internal", "Payment Gateway Operator", True),
    ]
    for i in range(11, 36):
        dept = ["Dev", "QA", "Analytics", "Support", "Finance"][i % 5]
        user_roles.append((f"User {i:02d}", f"user{i:02d}@cyberval.internal", f"{dept} Engineer", False))

    users = [User(display_name=name, email=email, role=role, privileged=priv) for name, email, role, priv in user_roles]
    db.add_all(users)
    db.flush()

    # 5. Assets (100 Enterprise Assets across Perimeter, DMZ, App, Data, Internal Tiers)
    assets: list[Asset] = []

    # Priority Named Assets (including PAYMENT-API-01 and core infrastructure)
    gateway = Asset(name="Internet Gateway", asset_type="network", environment="production", owner="Platform", internet_exposed=True, business_service=payment_svc)
    payment_api = Asset(name="PAYMENT-API-01", asset_type="application", environment="production", owner="Payments", internet_exposed=True, business_service=payment_svc)
    customer_db = Asset(name="Customer Database", asset_type="database", environment="production", owner="Data Office", internet_exposed=False, business_service=customer_svc)
    core_banking = Asset(name="Core Banking Server", asset_type="server", environment="production", owner="Banking Operations", internet_exposed=False, business_service=banking_svc)
    auth_service = Asset(name="AUTH-SERVICE-01", asset_type="application", environment="production", owner="SecOps & IAM", internet_exposed=True, business_service=identity_svc)
    waf_prod = Asset(name="WAF-PROD-01", asset_type="network", environment="production", owner="Platform", internet_exposed=True, business_service=payment_svc)
    bastion_host = Asset(name="Bastion Host", asset_type="server", environment="production", owner="Infrastructure", internet_exposed=True, business_service=identity_svc)
    checkout_svc = Asset(name="CHECKOUT-SVC-01", asset_type="application", environment="production", owner="Payments", internet_exposed=False, business_service=payment_svc)
    payment_db = Asset(name="Payment Core DB", asset_type="database", environment="production", owner="Payments", internet_exposed=False, business_service=payment_svc)
    identity_store = Asset(name="Identity LDAP Store", asset_type="database", environment="production", owner="SecOps & IAM", internet_exposed=False, business_service=identity_svc)

    assets.extend([gateway, payment_api, customer_db, core_banking, auth_service, waf_prod, bastion_host, checkout_svc, payment_db, identity_store])

    # Remaining 90 Assets across microservices, databases, internal clusters, workstations
    for idx in range(11, 101):
        svc = services[(idx % len(services))]
        if idx <= 25:
            name = f"APP-SVC-{idx:02d}"
            atype = "application"
            exposed = (idx % 3 == 0)
        elif idx <= 40:
            name = f"DATABASE-{idx:02d}"
            atype = "database"
            exposed = False
        elif idx <= 55:
            name = f"CACHE-QUEUE-{idx:02d}"
            atype = "middleware"
            exposed = False
        elif idx <= 70:
            name = f"INTERNAL-SRV-{idx:02d}"
            atype = "server"
            exposed = False
        elif idx <= 85:
            name = f"DEV-WS-{idx:02d}"
            atype = "workstation"
            exposed = False
        else:
            name = f"NETWORK-NODE-{idx:02d}"
            atype = "network"
            exposed = (idx % 2 == 0)

        assets.append(Asset(
            name=name,
            asset_type=atype,
            environment="production" if idx <= 80 else "staging",
            owner=svc.owner,
            internet_exposed=exposed,
            business_service=svc,
        ))

    db.add_all(assets)
    db.flush()

    # 6. Vulnerabilities (5 Key CVEs distributed across assets)
    vulnerabilities = [
        # CVE-2024-21762 on PAYMENT-API-01 and Internet Gateway (Perimeter / RCE)
        Vulnerability(cve_id="CVE-2024-21762", title="Fortinet FortiOS Out-of-Bound Write Remote Code Execution", cvss_score=Decimal("9.8"), severity="critical", status="open", asset=payment_api),
        Vulnerability(cve_id="CVE-2024-21762", title="Fortinet FortiOS Out-of-Bound Write Remote Code Execution", cvss_score=Decimal("9.8"), severity="critical", status="open", asset=gateway),
        # CVE-2024-3094 Supply chain compromise on auth service and app services
        Vulnerability(cve_id="CVE-2024-3094", title="XZ Utils Liblzma Backdoor Supply-chain Compromise", cvss_score=Decimal("10.0"), severity="critical", status="open", asset=auth_service),
        Vulnerability(cve_id="CVE-2024-3094", title="XZ Utils Liblzma Backdoor Supply-chain Compromise", cvss_score=Decimal("10.0"), severity="critical", status="open", asset=assets[10]),
        # CVE-2023-38606 Kernel Privilege Escalation
        Vulnerability(cve_id="CVE-2023-38606", title="Kernel Privilege Escalation Vulnerability", cvss_score=Decimal("9.8"), severity="critical", status="open", asset=bastion_host),
        Vulnerability(cve_id="CVE-2023-38606", title="Kernel Privilege Escalation Vulnerability", cvss_score=Decimal("9.8"), severity="critical", status="open", asset=core_banking),
        # CVE-2023-4863 Heap buffer overflow
        Vulnerability(cve_id="CVE-2023-4863", title="Libwebp Heap Buffer Overflow Code Execution", cvss_score=Decimal("8.8"), severity="high", status="open", asset=checkout_svc),
        # CVE-2023-44487 HTTP/2 Rapid Reset
        Vulnerability(cve_id="CVE-2023-44487", title="HTTP/2 Rapid Reset Denial of Service", cvss_score=Decimal("7.5"), severity="high", status="open", asset=waf_prod),
    ]
    db.add_all(vulnerabilities)
    db.flush()

    # 7. Telemetry Events (SIEM: 120, EDR: 60, CSPM: 35, IAM Access: 55+)
    now = datetime.now(UTC)
    telemetry_events: list[SecurityEvent] = []

    # Correlated Scenario for PAYMENT-API-01:
    # SIEM: Brute Force Authentication (T1110)
    telemetry_events.append(SecurityEvent(
        source="siem",
        event_type="Brute Force Authentication",
        severity="high",
        observed_at=now - timedelta(minutes=45),
        asset=payment_api,
        raw_payload=json.dumps({
            "technique": "T1110",
            "technique_name": "Brute Force",
            "failed_attempts": 284,
            "target_user": "bob.smith@cyberval.internal",
            "source_ip": "198.51.100.77",
            "port": 8443,
            "signature": "SIEM-AUTH-BRUTEFORCE-SUSPICIOUS",
        }),
    ))
    # EDR: Credential Dumping (T1003)
    telemetry_events.append(SecurityEvent(
        source="edr",
        event_type="Credential Dumping",
        severity="critical",
        observed_at=now - timedelta(minutes=25),
        asset=payment_api,
        raw_payload=json.dumps({
            "technique": "T1003",
            "technique_name": "OS Credential Dumping",
            "process": "mimikatz.exe",
            "target_process": "lsass.exe",
            "command_line": "sekurlsa::logonpasswords",
            "action": "memory_read_alert",
        }),
    ))
    # CSPM: Open Security Group Finding & MFA Disabled
    telemetry_events.append(SecurityEvent(
        source="cspm",
        event_type="Open Security Group",
        severity="high",
        observed_at=now - timedelta(hours=2),
        asset=payment_api,
        raw_payload=json.dumps({
            "finding": "Unrestricted Ingress 0.0.0.0/0 on Port 8443",
            "rule_id": "CIS-AWS-1.16",
            "resource": "sg-payment-api-prod",
            "mfa_disabled": True,
            "compliance_status": "NON_COMPLIANT",
        }),
    ))
    # IAM: Privileged Access Granted without MFA
    telemetry_events.append(SecurityEvent(
        source="iam",
        event_type="Privileged Access Permitted",
        severity="high",
        observed_at=now - timedelta(hours=3),
        asset=payment_api,
        raw_payload=json.dumps({
            "user_id": users[1].id,
            "user_email": users[1].email,
            "role": users[1].role,
            "access_type": "ssh_root",
            "privileged": True,
            "mfa_enabled": False,
            "session_type": "interactive",
        }),
    ))

    # Generate 119 more SIEM Events (Total 120 SIEM events)
    siem_types = [
        ("Suspicious Inbound SSH Connection", "high", "T1021.004"),
        ("Anomalous Outbound Data Transfer", "medium", "T1048"),
        ("Multiple Failed Login Attempts", "medium", "T1110"),
        ("Privilege Escalation Event", "high", "T1068"),
        ("Port Scan Detected", "low", "T1046"),
        ("Unusual DNS Query Volume", "medium", "T1071.004"),
    ]
    for i in range(1, 120):
        etype, sev, tech = siem_types[i % len(siem_types)]
        tgt_asset = assets[i % len(assets)]
        telemetry_events.append(SecurityEvent(
            source="siem",
            event_type=etype,
            severity=sev,
            observed_at=now - timedelta(minutes=i * 12),
            asset=tgt_asset,
            raw_payload=json.dumps({
                "technique": tech,
                "event_index": i,
                "source_ip": f"192.0.2.{i % 254}",
                "target_host": tgt_asset.name,
            }),
        ))

    # Generate 59 more EDR Events (Total 60 EDR events)
    edr_types = [
        ("Suspicious PowerShell Execution", "high", "T1059.001"),
        ("Process Injection Detected", "critical", "T1055"),
        ("Unrecognized Binary Execution in Temp Directory", "medium", "T1204"),
        ("Lateral Movement Remote Service Creation", "high", "T1543.003"),
        ("Defense Evasion - Log Clearing", "critical", "T1070.001"),
    ]
    for i in range(1, 60):
        etype, sev, tech = edr_types[i % len(edr_types)]
        tgt_asset = assets[(i * 3) % len(assets)]
        telemetry_events.append(SecurityEvent(
            source="edr",
            event_type=etype,
            severity=sev,
            observed_at=now - timedelta(minutes=i * 24),
            asset=tgt_asset,
            raw_payload=json.dumps({
                "technique": tech,
                "process_name": f"proc_{tech.replace('.', '_')}.exe",
                "pid": 1000 + i,
                "target_host": tgt_asset.name,
            }),
        ))

    # Generate 34 more CSPM Findings (Total 35 CSPM findings)
    cspm_types = [
        ("S3 Bucket Publicly Readable", "critical", "CIS-AWS-2.1.1"),
        ("Database Instance Unencrypted at Rest", "high", "CIS-AWS-2.3.1"),
        ("Unused Privileged IAM Role Active", "medium", "CIS-AWS-1.20"),
        ("Missing Web Application Firewall Attachment", "medium", "CIS-AWS-3.1"),
        ("Default VPC Security Group Ingress Open", "high", "CIS-AWS-5.1"),
    ]
    for i in range(1, 35):
        etype, sev, rule = cspm_types[i % len(cspm_types)]
        tgt_asset = assets[(i * 5) % len(assets)]
        telemetry_events.append(SecurityEvent(
            source="cspm",
            event_type=etype,
            severity=sev,
            observed_at=now - timedelta(hours=i * 2),
            asset=tgt_asset,
            raw_payload=json.dumps({
                "rule_id": rule,
                "resource_name": tgt_asset.name,
                "compliance_status": "FAILED",
            }),
        ))

    # Generate 54 IAM Access Permissions (Total 55+ IAM mappings)
    for i in range(54):
        u = users[i % len(users)]
        tgt_asset = assets[(i * 2) % len(assets)]
        access_type = "admin_ssh" if u.privileged else "read_api"
        telemetry_events.append(SecurityEvent(
            source="iam",
            event_type="Access Permission Established",
            severity="info" if not u.privileged else "medium",
            observed_at=now - timedelta(days=i),
            asset=tgt_asset,
            raw_payload=json.dumps({
                "user_id": u.id,
                "user_email": u.email,
                "role": u.role,
                "privileged": u.privileged,
                "access_type": access_type,
                "mfa_enabled": False if (u.privileged and i % 3 == 0) else True,
            }),
        ))

    db.add_all(telemetry_events)
    db.flush()

    # 8. Financial Risks (P1 baseline risk rows)
    risks = []
    for asset in assets:
        if asset.name == "PAYMENT-API-01":
            risks.append(Risk(asset=asset, likelihood=Decimal("0.45"), financial_impact=Decimal("95000000"), expected_annual_loss=Decimal("42750000"), confidence=Decimal("0.91")))
        elif asset.name == "Internet Gateway":
            risks.append(Risk(asset=asset, likelihood=Decimal("0.35"), financial_impact=Decimal("38000000"), expected_annual_loss=Decimal("13300000"), confidence=Decimal("0.85")))
        elif asset.name == "Customer Database":
            risks.append(Risk(asset=asset, likelihood=Decimal("0.22"), financial_impact=Decimal("64000000"), expected_annual_loss=Decimal("14080000"), confidence=Decimal("0.82")))
        elif asset.name == "Core Banking Server":
            risks.append(Risk(asset=asset, likelihood=Decimal("0.18"), financial_impact=Decimal("120000000"), expected_annual_loss=Decimal("21600000"), confidence=Decimal("0.88")))
        elif asset.internet_exposed:
            risks.append(Risk(asset=asset, likelihood=Decimal("0.15"), financial_impact=Decimal("15000000"), expected_annual_loss=Decimal("2250000"), confidence=Decimal("0.75")))
        else:
            risks.append(Risk(asset=asset, likelihood=Decimal("0.05"), financial_impact=Decimal("8000000"), expected_annual_loss=Decimal("400000"), confidence=Decimal("0.70")))

    db.add_all(risks)

    # 9. Investments
    investments = [
        Investment(name="Privileged Access MFA Enforcement", description="Extend phishing-resistant MFA to all privileged administrative paths.", cost=Decimal("2500000"), risk_reduction=Decimal("12500000"), implementation_days=30),
        Investment(name="Critical Patching Sprint (CVE-2024-21762)", description="Remediate internet-facing critical perimeter vulnerabilities.", cost=Decimal("1500000"), risk_reduction=Decimal("18000000"), implementation_days=14),
        Investment(name="Zero-Trust Microsegmentation", description="Enforce granular microsegmentation between application tiers and databases.", cost=Decimal("5000000"), risk_reduction=Decimal("15000000"), implementation_days=45),
        Investment(name="Advanced EDR Memory Protection", description="Deploy anti-mimikatz and LSASS credential protection on all servers.", cost=Decimal("3000000"), risk_reduction=Decimal("9000000"), implementation_days=21),
    ]
    db.add_all(investments)

    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed(session)
    print("CYBERVAL enterprise dataset seeded successfully.")
