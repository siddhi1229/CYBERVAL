from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Asset, CveCatalogRecord, Vulnerability
from seed import seed


def test_seed_execution_and_risk_signals():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    seed(session)

    # 1. Verify CVE catalog records
    catalog_count = session.query(CveCatalogRecord).count()
    assert catalog_count == 5

    fortinet_cat = session.get(CveCatalogRecord, "CVE-2024-21762")
    assert fortinet_cat is not None
    assert fortinet_cat.cvss_score == Decimal("9.8")
    assert fortinet_cat.known_exploited is True
    assert fortinet_cat.severity == "CRITICAL"

    xz_cat = session.get(CveCatalogRecord, "CVE-2024-3094")
    assert xz_cat is not None
    assert xz_cat.cvss_score == Decimal("10.0")
    assert xz_cat.known_exploited is False

    # 2. Verify Asset associations & composite risk signals
    vulns = session.query(Vulnerability).all()
    assert len(vulns) == 4

    gw_asset = session.query(Asset).filter_by(name="Internet Gateway").one()
    gw_cve = session.query(Vulnerability).filter_by(cve_id="CVE-2024-21762", asset_id=gw_asset.id).one()
    assert gw_asset.internet_exposed is True
    assert gw_cve.known_exploited is True
    assert gw_cve.composite_risk_priority == "CRITICAL_EXPLOITED_EXPOSED"

    pay_asset = session.query(Asset).filter_by(name="Payment API").one()
    payment_xz = session.query(Vulnerability).filter_by(cve_id="CVE-2024-3094", asset_id=pay_asset.id).one()
    assert payment_xz.composite_risk_priority == "HIGH_EXPOSED_CRITICAL"

    session.close()
