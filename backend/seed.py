from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Asset, BusinessService, Control, FrameworkControl, Investment, Risk, Threat, Vulnerability


def seed(db: Session) -> None:
    if db.query(Asset).first():
        return
    payment = BusinessService(name="Payment Service", owner="Digital Commerce", criticality="critical", annual_revenue=Decimal("480000000"))
    customer = BusinessService(name="Customer Data Platform", owner="Data Office", criticality="high", annual_revenue=Decimal("260000000"))
    db.add_all([payment, customer])
    db.flush()
    assets = [Asset(name="Internet Gateway", asset_type="network", owner="Platform", internet_exposed=True, business_service=payment), Asset(name="Payment API", asset_type="application", owner="Payments", internet_exposed=True, business_service=payment), Asset(name="Customer Database", asset_type="database", owner="Data Office", business_service=customer)]
    db.add_all(assets)
    db.flush()
    db.add_all([Vulnerability(cve_id="CVE-2024-21762", title=" perimeter appliance remote execution", cvss_score=Decimal("9.8"), severity="critical", asset=assets[0]), Vulnerability(cve_id="CVE-2024-3094", title="Supply-chain compromise", cvss_score=Decimal("10.0"), severity="critical", asset=assets[1])])
    db.add_all([Threat(name="Ransomware", category="malware", annual_frequency=Decimal("0.18"), source="synthetic threat intelligence"), Threat(name="Credential Theft", category="identity", annual_frequency=Decimal("0.32"), source="synthetic threat intelligence")])
    controls = [Control(name="Multi-factor Authentication", description="Require phishing-resistant MFA for privileged access.", effectiveness=Decimal("0.72")), Control(name="Critical Vulnerability Patching", description="Patch exploitable critical vulnerabilities within defined SLA.", effectiveness=Decimal("0.68")), Control(name="Network Segmentation", description="Restrict movement between internet-facing and sensitive services.", effectiveness=Decimal("0.61"))]
    db.add_all(controls)
    db.flush()
    db.add_all([Risk(asset=assets[0], likelihood=Decimal("0.24"), financial_impact=Decimal("18000000"), expected_annual_loss=Decimal("4320000"), confidence=Decimal("0.82")), Risk(asset=assets[1], likelihood=Decimal("0.19"), financial_impact=Decimal("47000000"), expected_annual_loss=Decimal("8930000"), confidence=Decimal("0.79")), Risk(asset=assets[2], likelihood=Decimal("0.11"), financial_impact=Decimal("31000000"), expected_annual_loss=Decimal("3410000"), confidence=Decimal("0.76"))])
    db.add_all([Investment(name="Privileged Access MFA", description="Extend phishing-resistant MFA to privileged paths.", cost=Decimal("2500000"), risk_reduction=Decimal("4200000"), implementation_days=45), Investment(name="Critical Patching Sprint", description="Remediate internet-facing critical vulnerabilities.", cost=Decimal("1500000"), risk_reduction=Decimal("5100000"), implementation_days=30), Investment(name="Service Segmentation", description="Segment payment and data service trust zones.", cost=Decimal("4000000"), risk_reduction=Decimal("3600000"), implementation_days=60)])
    for framework in ["NIST CSF", "ISO/IEC 27001", "CIS Controls", "RBI CSF", "SEBI CSCRF"]:
        for control in controls:
            db.add(FrameworkControl(framework=framework, control_code=f"{framework[:3].upper()}-{control.id}", control_name=control.name, master_control_id=control.id))
    db.commit()


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed(session)
    print("Synthetic CYBERVAL seed data loaded")
