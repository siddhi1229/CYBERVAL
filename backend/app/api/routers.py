from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Asset, Control, FrameworkControl, Investment, Risk, Threat, Vulnerability
from app.services.graph_service import CyberRiskDigitalTwin
from app.services.ingestion import NormalizedIngestionService
from app.schemas.contracts import (
    AssetCorrelationRead, AssetDependencyRead, AssetRead, AttackPathRead,
    ComplianceRead, ControlRead, CytoscapeGraphResponse, EnterpriseRiskRead,
    OptimizationRead, OptimizationRequest, RecommendationRead, RecommendationRequest,
    RiskRead, SimulationRead, SimulationRequest, ThreatRead, VulnerabilityRead,
    IngestionRead, IngestionRequest,
)
from app.schemas.contracts import (
    AssetCorrelationRead,
    AssetRead,
    AssetVulnerabilityAssociationRequest,
    AttackPathRead,
    ComplianceRead,
    ControlRead,
    CspmFindingRead,
    CveCatalogRecordRead,
    CveCatalogSyncRead,
    CveCatalogSyncRequest,
    EdrEventRead,
    EnterpriseRiskRead,
    EnterpriseSyncRead,
    IngestionRead,
    IngestionRequest,
    OptimizationRead,
    OptimizationRequest,
    RecommendationRead,
    RecommendationRequest,
    RiskRead,
    SecurityEventRead,
    SimulationRead,
    SimulationRequest,
    ThreatRead,
    UserAssetAccessRead,
    UserRead,
    VulnerabilityRead,
)
from app.services.correlator import CveCorrelatorService
from app.services.ingestion import NormalizedIngestionService

router = APIRouter(prefix="/api")
correlator_service = CveCorrelatorService()
ingestion_service = NormalizedIngestionService(correlator=correlator_service)


@router.post("/ingestion", response_model=IngestionRead, summary="Normalize telemetry into shared entities")
def ingest_telemetry(request: IngestionRequest, db: Session = Depends(get_db)):
    count = ingestion_service.ingest(db, request.source, request.records)
    return IngestionRead(source=request.source, records_ingested=count)


@router.post("/ingestion/sync-enterprise", response_model=EnterpriseSyncRead, summary="Orchestrated sync of all 5 simulated sources into PostgreSQL")
def sync_enterprise_data(
    asset_count: int = Query(default=100, ge=1, le=500),
    user_count: int = Query(default=35, ge=1, le=200),
    siem_count: int = Query(default=120, ge=1, le=1000),
    edr_count: int = Query(default=60, ge=1, le=500),
    cspm_count: int = Query(default=35, ge=1, le=200),
    db: Session = Depends(get_db),
):
    result = ingestion_service.sync_enterprise(
        db,
        asset_count=asset_count,
        user_count=user_count,
        siem_count=siem_count,
        edr_count=edr_count,
        cspm_count=cspm_count,
    )
    return EnterpriseSyncRead(**result)


@router.post("/ingestion/assets/sync", response_model=IngestionRead, summary="Sync enterprise asset inventory")
def sync_assets_endpoint(count: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)):
    ingested = ingestion_service.asset_adapter.ingest(db, count=count)
    return IngestionRead(source="asset_inventory", records_ingested=ingested)


@router.post("/ingestion/iam/sync", response_model=IngestionRead, summary="Sync IAM identities and access grants")
def sync_iam_endpoint(count: int = Query(default=35, ge=1, le=200), db: Session = Depends(get_db)):
    ingested = ingestion_service.iam_adapter.ingest(db, count=count)
    return IngestionRead(source="iam", records_ingested=ingested)


@router.post("/ingestion/siem/sync", response_model=IngestionRead, summary="Sync SIEM security event telemetry")
def sync_siem_endpoint(count: int = Query(default=120, ge=1, le=1000), db: Session = Depends(get_db)):
    ingested = ingestion_service.siem_adapter.ingest(db, count=count)
    return IngestionRead(source="siem", records_ingested=ingested)


@router.post("/ingestion/edr/sync", response_model=IngestionRead, summary="Sync EDR endpoint telemetry")
def sync_edr_endpoint(count: int = Query(default=60, ge=1, le=500), db: Session = Depends(get_db)):
    ingested = ingestion_service.edr_adapter.ingest(db, count=count)
    return IngestionRead(source="edr", records_ingested=ingested)


@router.post("/ingestion/cspm/sync", response_model=IngestionRead, summary="Sync CSPM cloud posture findings")
def sync_cspm_endpoint(count: int = Query(default=35, ge=1, le=200), db: Session = Depends(get_db)):
    ingested = ingestion_service.cspm_adapter.ingest(db, count=count)
    return IngestionRead(source="cspm", records_ingested=ingested)


@router.get("/assets", response_model=list[AssetRead], summary="List normalized assets")
def list_assets(
    criticality: str | None = Query(default=None, description="Filter by criticality (LOW, MEDIUM, HIGH, CRITICAL)"),
    asset_type: str | None = Query(default=None, description="Filter by asset type"),
    internet_exposed: bool | None = Query(default=None, description="Filter by internet exposure"),
    department: str | None = Query(default=None, description="Filter by department"),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Asset).order_by(Asset.id)
    if criticality:
        stmt = stmt.where(Asset.criticality == criticality.upper())
    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type.lower())
    if internet_exposed is not None:
        stmt = stmt.where(Asset.internet_exposed == internet_exposed)
    if department:
        stmt = stmt.where(Asset.department == department)
    return db.scalars(stmt.limit(limit)).all()


@router.get("/security-events", response_model=list[SecurityEventRead], summary="List SIEM security events")
def list_security_events(
    asset_id: int | None = Query(default=None),
    severity: str | None = Query(default=None),
    event_type: str | None = Query(default=None),
    source: str | None = Query(default=None),
    technique: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(SecurityEvent).options(joinedload(SecurityEvent.asset)).order_by(SecurityEvent.observed_at.desc())
    if asset_id is not None:
        stmt = stmt.where(SecurityEvent.asset_id == asset_id)
    if severity:
        stmt = stmt.where(SecurityEvent.severity == severity.lower())
    if event_type:
        stmt = stmt.where(SecurityEvent.event_type == event_type.upper())
    if source:
        stmt = stmt.where(SecurityEvent.source == source)
    if technique:
        stmt = stmt.where(SecurityEvent.technique.ilike(f"%{technique}%"))
    events = db.scalars(stmt.limit(limit)).all()
    return [
        SecurityEventRead(
            id=e.id,
            event_id_code=e.event_id_code,
            source=e.source,
            event_type=e.event_type,
            severity=e.severity,
            observed_at=e.observed_at,
            source_ip=e.source_ip,
            technique=e.technique,
            description=e.description,
            user_id_code=e.user_id_code,
            user_id=e.user_id,
            asset_id=e.asset_id,
            asset_name=e.asset.name if e.asset else None,
        )
        for e in events
    ]


@router.get("/iam/users", response_model=list[UserRead], summary="List enterprise IAM user identities")
def list_iam_users(
    privilege_level: str | None = Query(default=None),
    privileged: bool | None = Query(default=None),
    mfa_enabled: bool | None = Query(default=None),
    risky_login: bool | None = Query(default=None),
    department: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(User).order_by(User.id)
    if privilege_level:
        stmt = stmt.where(User.privilege_level == privilege_level.lower())
    if privileged is not None:
        stmt = stmt.where(User.privileged == privileged)
    if mfa_enabled is not None:
        stmt = stmt.where(User.mfa_enabled == mfa_enabled)
    if risky_login is not None:
        stmt = stmt.where(User.risky_login == risky_login)
    if department:
        stmt = stmt.where(User.department == department)
    return db.scalars(stmt.limit(limit)).all()


@router.get("/iam/access", response_model=list[UserAssetAccessRead], summary="List user-asset access graph")
def list_iam_access(
    user_id: int | None = Query(default=None),
    asset_id: int | None = Query(default=None),
    access_level: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = (
        select(UserAssetAccess)
        .options(joinedload(UserAssetAccess.user), joinedload(UserAssetAccess.asset))
        .order_by(UserAssetAccess.id)
    )
    if user_id is not None:
        stmt = stmt.where(UserAssetAccess.user_id == user_id)
    if asset_id is not None:
        stmt = stmt.where(UserAssetAccess.asset_id == asset_id)
    if access_level:
        stmt = stmt.where(UserAssetAccess.access_level == access_level.lower())

    rows = db.scalars(stmt.limit(limit)).all()
    return [
        UserAssetAccessRead(
            id=r.id,
            user_id=r.user_id,
            asset_id=r.asset_id,
            access_level=r.access_level,
            status=r.status,
            granted_at=getattr(r, "granted_at", None) or getattr(r, "created_at", None) or datetime.now(UTC),
            user_id_code=r.user.user_id_code if r.user else None,
            username=r.user.username if r.user else None,
            asset_id_code=r.asset.asset_id_code if r.asset else None,
            asset_name=r.asset.name if r.asset else None,
        )
        for r in rows
    ]


@router.get("/edr/events", response_model=list[EdrEventRead], summary="List EDR endpoint events")
def list_edr_events(
    endpoint_id: str | None = Query(default=None),
    asset_id: int | None = Query(default=None),
    event_type: str | None = Query(default=None),
    indicator: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(EdrEvent).order_by(EdrEvent.observed_at.desc())
    if endpoint_id:
        stmt = stmt.where(EdrEvent.endpoint_id == endpoint_id.upper())
    if asset_id is not None:
        stmt = stmt.where(EdrEvent.asset_id == asset_id)
    if event_type:
        stmt = stmt.where(EdrEvent.event_type == event_type.upper())
    if indicator:
        stmt = stmt.where(EdrEvent.indicator.ilike(f"%{indicator}%"))
    if severity:
        stmt = stmt.where(EdrEvent.severity == severity.lower())
    return db.scalars(stmt.limit(limit)).all()


@router.get("/cspm/findings", response_model=list[CspmFindingRead], summary="List CSPM cloud posture findings")
def list_cspm_findings(
    resource_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    finding_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    internet_exposed: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(CspmFinding).order_by(CspmFinding.id)
    if resource_id:
        stmt = stmt.where(CspmFinding.resource_id == resource_id.upper())
    if resource_type:
        stmt = stmt.where(CspmFinding.resource_type == resource_type.upper())
    if finding_type:
        stmt = stmt.where(CspmFinding.finding_type == finding_type.upper())
    if severity:
        stmt = stmt.where(CspmFinding.severity == severity.lower())
    if internet_exposed is not None:
        stmt = stmt.where(CspmFinding.internet_exposed == internet_exposed)
    return db.scalars(stmt.limit(limit)).all()


@router.get("/correlation/asset/{asset_identifier}", response_model=AssetCorrelationRead, summary="360-degree security correlation across all sources for an asset")
def get_asset_correlation(asset_identifier: str, db: Session = Depends(get_db)):
    """Retrieve unified posture across Asset, NVD/KEV Vulnerabilities, SIEM Events, EDR Events, CSPM Findings, and IAM Users."""
    asset = None
    if asset_identifier.isdigit():
        asset = db.get(Asset, int(asset_identifier))
    if not asset:
        asset = db.scalar(
            select(Asset).where(
                (Asset.asset_id_code == asset_identifier.upper())
                | (Asset.name.ilike(asset_identifier))
            )
        )
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_identifier}' not found.")

    # Correlated vulnerabilities
    vulns = db.scalars(
        select(Vulnerability)
        .options(joinedload(Vulnerability.asset).joinedload(Asset.business_service))
        .where(Vulnerability.asset_id == asset.id)
    ).unique().all()
    vuln_reads = [_format_vulnerability(v) for v in vulns]

    # Correlated SIEM events
    events = db.scalars(
        select(SecurityEvent)
        .options(joinedload(SecurityEvent.asset))
        .where(SecurityEvent.asset_id == asset.id)
        .order_by(SecurityEvent.observed_at.desc())
        .limit(20)
    ).all()
    evt_reads = [
        SecurityEventRead(
            id=e.id,
            event_id_code=e.event_id_code,
            source=e.source,
            event_type=e.event_type,
            severity=e.severity,
            observed_at=e.observed_at,
            source_ip=e.source_ip,
            technique=e.technique,
            description=e.description,
            user_id_code=e.user_id_code,
            user_id=e.user_id,
            asset_id=e.asset_id,
            asset_name=asset.name,
        )
        for e in events
    ]

    # Correlated EDR events
    edr_events = db.scalars(
        select(EdrEvent)
        .where(
            (EdrEvent.asset_id == asset.id)
            | (EdrEvent.endpoint_id == (asset.asset_id_code or asset.name).upper())
        )
        .order_by(EdrEvent.observed_at.desc())
        .limit(20)
    ).all()
    edr_reads = [
        EdrEventRead(
            id=edr.id,
            event_id_code=edr.event_id_code,
            endpoint_id=edr.endpoint_id,
            asset_id=edr.asset_id,
            user_id_code=edr.user_id_code,
            user_id=edr.user_id,
            event_type=edr.event_type,
            process_name=edr.process_name,
            process_path=edr.process_path,
            indicator=edr.indicator,
            severity=edr.severity,
            observed_at=edr.observed_at,
        )
        for edr in edr_events
    ]

    # Correlated CSPM findings
    cspm_findings = db.scalars(
        select(CspmFinding)
        .where(
            (CspmFinding.asset_id == asset.id)
            | (CspmFinding.resource_id == (asset.asset_id_code or asset.name).upper())
        )
    ).all()
    cspm_reads = [
        CspmFindingRead(
            id=f.id,
            finding_id_code=f.finding_id_code,
            provider=f.provider,
            resource_id=f.resource_id,
            resource_type=f.resource_type,
            finding_type=f.finding_type,
            description=f.description,
            severity=f.severity,
            status=f.status,
            internet_exposed=f.internet_exposed,
            encrypted=f.encrypted,
            remediation=f.remediation,
            asset_id=f.asset_id,
        )
        for f in cspm_findings
    ]

    # Correlated IAM users
    access_rows = db.scalars(
        select(UserAssetAccess)
        .options(joinedload(UserAssetAccess.user))
        .where(UserAssetAccess.asset_id == asset.id)
    ).all()
    users = [r.user for r in access_rows if r.user]
    user_reads = [UserRead.model_validate(u) for u in users]

    # Calculate composite security summary for P1 output
    known_exploited_count = sum(1 for v in vuln_reads if v.known_exploited)
    max_cvss = max((v.cvss_score for v in vuln_reads), default=Decimal("0.0"))
    has_un_mfad_privileged_user = any(u.privileged and not u.mfa_enabled for u in user_reads)
    critical_siem_alerts = sum(1 for e in evt_reads if e.severity == "critical")
    critical_edr_alerts = sum(1 for e in edr_reads if e.severity == "critical")
    critical_cspm = sum(1 for c in cspm_reads if c.severity == "critical")

    is_high_risk_target = bool(
        asset.internet_exposed
        and asset.criticality == "CRITICAL"
        and known_exploited_count > 0
        and has_un_mfad_privileged_user
    )

    summary = {
        "asset_id_code": asset.asset_id_code,
        "criticality": asset.criticality,
        "business_value": float(asset.business_value),
        "internet_exposed": asset.internet_exposed,
        "total_vulnerabilities": len(vuln_reads),
        "known_exploited_vulnerabilities": known_exploited_count,
        "max_cvss_score": float(max_cvss),
        "has_unmfa_privileged_access": has_un_mfad_privileged_user,
        "critical_siem_events": critical_siem_alerts,
        "critical_edr_events": critical_edr_alerts,
        "critical_cspm_findings": critical_cspm,
        "is_high_risk_attack_target": is_high_risk_target,
    }

    return AssetCorrelationRead(
        asset=AssetRead.model_validate(asset),
        vulnerabilities=vuln_reads,
        security_events=evt_reads,
        edr_events=edr_reads,
        cspm_findings=cspm_reads,
        authorized_users=user_reads,
        composite_risk_summary=summary,
    )


@router.post("/ingestion/sync-all", response_model=CveCatalogSyncRead, summary="Fetch NVD + CISA KEV, correlate, and enrich asset vulnerabilities")
def sync_all_vulnerabilities(request: CveCatalogSyncRequest = CveCatalogSyncRequest(), db: Session = Depends(get_db)):
    kev_count, nvd_count, catalog_count = correlator_service.sync_catalog(
        db,
        cve_ids=request.cve_ids if request.cve_ids else None,
        sync_cisa_kev=request.sync_cisa_kev,
        sync_nvd=request.sync_nvd,
    )
    enriched_count = 0
    if request.enrich_asset_vulnerabilities:
        enriched_count = correlator_service.enrich_asset_vulnerabilities(db)

    return CveCatalogSyncRead(
        cisa_kev_count=kev_count,
        nvd_count=nvd_count,
        correlated_catalog_count=catalog_count,
        asset_vulnerabilities_enriched=enriched_count,
        timestamp=datetime.now(UTC),
    )


@router.post("/ingestion/cisa-kev/sync", response_model=CveCatalogSyncRead, summary="Fetch and sync CISA KEV catalog")
def sync_cisa_kev(db: Session = Depends(get_db)):
    kev_count, nvd_count, catalog_count = correlator_service.sync_catalog(
        db,
        sync_cisa_kev=True,
        sync_nvd=False,
    )
    enriched = correlator_service.enrich_asset_vulnerabilities(db)
    return CveCatalogSyncRead(
        cisa_kev_count=kev_count,
        nvd_count=nvd_count,
        correlated_catalog_count=catalog_count,
        asset_vulnerabilities_enriched=enriched,
        timestamp=datetime.now(UTC),
    )


@router.post("/ingestion/nvd/sync", response_model=CveCatalogSyncRead, summary="Fetch and sync target CVEs from NVD")
def sync_nvd(request: CveCatalogSyncRequest, db: Session = Depends(get_db)):
    kev_count, nvd_count, catalog_count = correlator_service.sync_catalog(
        db,
        cve_ids=request.cve_ids,
        sync_cisa_kev=False,
        sync_nvd=True,
    )
    enriched = correlator_service.enrich_asset_vulnerabilities(db) if request.enrich_asset_vulnerabilities else 0
    return CveCatalogSyncRead(
        cisa_kev_count=kev_count,
        nvd_count=nvd_count,
        correlated_catalog_count=catalog_count,
        asset_vulnerabilities_enriched=enriched,
        timestamp=datetime.now(UTC),
    )


@router.get("/vulnerabilities/catalog", response_model=list[CveCatalogRecordRead], summary="Search normalized CVE catalog")
def list_cve_catalog(
    query: str | None = Query(default=None, description="Search term in CVE ID, title, or affected product"),
    known_exploited: bool | None = Query(default=None, description="Filter by CISA KEV known exploited flag"),
    min_cvss: float | None = Query(default=None, description="Minimum CVSS base score"),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(CveCatalogRecord)
    if known_exploited is not None:
        stmt = stmt.where(CveCatalogRecord.known_exploited == known_exploited)
    if min_cvss is not None:
        stmt = stmt.where(CveCatalogRecord.cvss_score >= Decimal(str(min_cvss)))
    if query:
        q = f"%{query.strip()}%"
        stmt = stmt.where(
            CveCatalogRecord.cve_id.ilike(q)
            | CveCatalogRecord.title.ilike(q)
            | CveCatalogRecord.affected_product.ilike(q)
            | CveCatalogRecord.affected_vendor.ilike(q)
        )
    stmt = stmt.order_by(CveCatalogRecord.cvss_score.desc(), CveCatalogRecord.known_exploited.desc()).limit(limit)
    return db.scalars(stmt).all()


@router.get("/vulnerabilities/catalog/{cve_id}", response_model=CveCatalogRecordRead, summary="Get normalized CVE details")
def get_cve_catalog_item(cve_id: str, db: Session = Depends(get_db)):
    item = db.get(CveCatalogRecord, cve_id.strip().upper())
    if not item:
        # Attempt on-demand sync
        try:
            correlator_service.sync_catalog(db, cve_ids=[cve_id.strip().upper()], sync_cisa_kev=True, sync_nvd=True)
            item = db.get(CveCatalogRecord, cve_id.strip().upper())
        except Exception:
            pass
    if not item:
        raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found in catalog.")
    return item


@router.post("/vulnerabilities/associate", response_model=VulnerabilityRead, summary="Associate a normalized CVE with an asset")
def associate_vulnerability(request: AssetVulnerabilityAssociationRequest, db: Session = Depends(get_db)):
    try:
        vuln = correlator_service.associate_cve_with_asset(
            db,
            cve_id=request.cve_id,
            asset_id=request.asset_id,
            status=request.status,
            custom_title=request.custom_title,
        )
        return _format_vulnerability(vuln)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


def _format_vulnerability(v: Vulnerability) -> VulnerabilityRead:
    crit = v.asset.business_service.criticality if (v.asset and v.asset.business_service) else None
    return VulnerabilityRead(
        id=v.id,
        cve_id=v.cve_id,
        title=v.title,
        description=v.description,
        cvss_score=v.cvss_score,
        severity=v.severity,
        status=v.status,
        known_exploited=v.known_exploited,
        kev_date_added=v.kev_date_added,
        kev_due_date=v.kev_due_date,
        known_ransomware_use=v.known_ransomware_use,
        affected_product=v.affected_product,
        cwe_id=v.cwe_id,
        required_action=v.required_action,
        sources=v.sources,
        composite_risk_priority=v.composite_risk_priority,
        asset_id=v.asset_id,
        asset_name=v.asset.name if v.asset else None,
        internet_exposed=v.asset.internet_exposed if v.asset else False,
        business_service_criticality=crit,
    )


@router.get("/vulnerabilities", response_model=list[VulnerabilityRead], summary="List asset vulnerabilities with KEV & risk context")
def list_vulnerabilities(
    known_exploited: bool | None = Query(default=None, description="Filter by KEV exploited status"),
    internet_exposed: bool | None = Query(default=None, description="Filter by internet exposure of asset"),
    severity: str | None = Query(default=None, description="Filter by vulnerability severity"),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Vulnerability)
        .options(
            joinedload(Vulnerability.asset).joinedload(Asset.business_service)
        )
        .order_by(Vulnerability.known_exploited.desc(), Vulnerability.cvss_score.desc(), Vulnerability.id)
    )
    if known_exploited is not None:
        stmt = stmt.where(Vulnerability.known_exploited == known_exploited)
    if severity is not None:
        stmt = stmt.where(Vulnerability.severity == severity.lower())
    if internet_exposed is not None:
        stmt = stmt.join(Vulnerability.asset).where(Asset.internet_exposed == internet_exposed)

    vulns = db.scalars(stmt).unique().all()
    return [_format_vulnerability(v) for v in vulns]


@router.get("/threats", response_model=list[ThreatRead], summary="List threat intelligence")
def list_threats(db: Session = Depends(get_db)):
    return db.scalars(select(Threat).order_by(Threat.id)).all()


@router.get("/controls", response_model=list[ControlRead], summary="List master security controls")
def list_controls(db: Session = Depends(get_db)):
    return db.scalars(select(Control).order_by(Control.id)).all()


# ==========================================
# P3 Digital Twin & Graph Endpoints
# ==========================================

@router.get("/graph", response_model=CytoscapeGraphResponse, summary="Get Cytoscape-compatible enterprise digital twin graph")
def get_digital_twin_graph(db: Session = Depends(get_db)):
    digital_twin = CyberRiskDigitalTwin(db)
    return digital_twin.get_cytoscape_data()


@router.get("/attack-paths", response_model=list[AttackPathRead], summary="Discover and score prioritized attack paths")
def attack_paths(
    limit: int = Query(20, ge=1, le=100, description="Max number of attack paths to return"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum path risk score"),
    target_asset_id: int | None = Query(None, description="Filter paths targeting a specific asset ID"),
    db: Session = Depends(get_db),
):
    digital_twin = CyberRiskDigitalTwin(db)
    paths = digital_twin.discover_attack_paths(limit=limit, min_score=min_score, target_asset_id=target_asset_id)
    return paths


@router.get("/assets/{asset_id}/dependencies", response_model=AssetDependencyRead, summary="Get asset dependencies, connections, and blast radius")
def get_asset_dependencies(asset_id: int, db: Session = Depends(get_db)):
    digital_twin = CyberRiskDigitalTwin(db)
    deps = digital_twin.get_asset_dependencies(asset_id)
    if not deps:
        raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found in graph")
    return deps


@router.get("/assets/{asset_id}/attack-paths", response_model=list[AttackPathRead], summary="Get attack paths traversing or targeting an asset")
def get_asset_attack_paths(asset_id: int, db: Session = Depends(get_db)):
    digital_twin = CyberRiskDigitalTwin(db)
    all_paths = digital_twin.discover_attack_paths(limit=50)
    asset_node_id = f"asset-{asset_id}"
    asset = db.scalar(select(Asset).where(Asset.id == asset_id))
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset with ID {asset_id} not found")

    filtered = [p for p in all_paths if asset_node_id in p.nodes or any(asset.name in ca for ca in p.critical_assets)]
    return filtered


@router.get("/correlation/asset/{asset_id}", response_model=AssetCorrelationRead, summary="Get multi-source telemetry convergence for an asset")
def correlate_asset(asset_id: str, db: Session = Depends(get_db)):
    digital_twin = CyberRiskDigitalTwin(db)
    result = digital_twin.correlate_asset_sources(asset_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found for telemetry correlation")
    return result


# ==========================================
# Financial Risk & Decision Support (P1/P2)
# ==========================================

@router.get("/risk/enterprise", response_model=EnterpriseRiskRead, summary="Get enterprise financial risk")
def enterprise_risk(db: Session = Depends(get_db)):
    total, count = db.execute(select(func.coalesce(func.sum(Risk.expected_annual_loss), 0), func.count(Risk.id))).one()
    highest = db.scalar(select(Risk.asset_id).order_by(Risk.expected_annual_loss.desc()).limit(1))
    return EnterpriseRiskRead(total_expected_annual_loss=total, risk_count=count, highest_risk_asset_id=highest, calculation_version="baseline-1")


@router.get("/risk/assets", response_model=list[RiskRead], summary="Get financial risk by asset")
def asset_risk(db: Session = Depends(get_db)):
    return db.scalars(select(Risk).order_by(Risk.expected_annual_loss.desc())).all()


@router.post("/ai/recommend", response_model=RecommendationRead, summary="Request a risk-grounded recommendation")
def recommend(request: RecommendationRequest, db: Session = Depends(get_db)):
    risk = db.scalar(select(Risk).order_by(Risk.expected_annual_loss.desc()).limit(1))
    return RecommendationRead(answer="Risk-grounded recommendation requires the decision-support module.", source_risk_ids=[risk.id] if risk else [], generated_at=datetime.now(UTC))


@router.post("/ai/query", response_model=RecommendationRead, summary="Ask a risk-grounded question")
def query_ai(request: RecommendationRequest, db: Session = Depends(get_db)):
    return recommend(request, db)


@router.post("/simulation/run", response_model=SimulationRead, summary="Run a what-if simulation")
def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
    total = db.scalar(select(func.coalesce(func.sum(Risk.expected_annual_loss), 0))) or Decimal("0")
    return SimulationRead(iterations=request.iterations, mean_loss=total, median_loss=total, p90_loss=total, p95_loss=total, p99_loss=total)


@router.post("/investments/optimize", response_model=OptimizationRead, summary="Optimize investments under a budget")
def optimize(request: OptimizationRequest, db: Session = Depends(get_db)):
    investments = db.scalars(select(Investment).where(Investment.status == "available").order_by(Investment.risk_reduction.desc())).all()
    selected = []
    remaining = request.budget
    reduction = Decimal("0")
    for investment in investments:
        if investment.cost <= remaining:
            selected.append(investment.id)
            remaining -= investment.cost
            reduction += investment.risk_reduction
    return OptimizationRead(budget=request.budget, selected_investment_ids=selected, projected_risk_reduction=reduction, remaining_budget=remaining)


@router.get("/compliance", response_model=list[ComplianceRead], summary="Get framework control coverage")
def compliance(db: Session = Depends(get_db)):
    rows = db.execute(select(FrameworkControl.framework, func.count(FrameworkControl.id)).group_by(FrameworkControl.framework)).all()
    return [ComplianceRead(framework=framework, mapped_controls=count, total_controls=count) for framework, count in rows]
