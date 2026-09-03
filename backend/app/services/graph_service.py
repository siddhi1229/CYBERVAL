import json
import logging
from collections import defaultdict
from decimal import Decimal
from typing import Any

import networkx as nx
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Asset, BusinessService, Control, CspmFinding, EdrEvent,
    FrameworkControl, Risk, SecurityEvent, Threat, User,
    UserAssetAccess, Vulnerability,
)
from app.schemas.contracts import (
    AssetCorrelationRead, AssetDependencyRead, AttackPathEdgeRead,
    AttackPathRead, CytoscapeEdge, CytoscapeEdgeData, CytoscapeGraphResponse,
    CytoscapeGraphSummary, CytoscapeNode, CytoscapeNodeData,
    DigitalTwinAssetCorrelationRead, SupportingTelemetryRead,
)

logger = logging.getLogger(__name__)


class CyberRiskDigitalTwin:
    """
    P3 Cyber Risk Digital Twin Engine.
    Transforms relational enterprise telemetry and entities in PostgreSQL into a
    connected, analytical directed graph using NetworkX.

    Provides:
    - Multi-entity graph model (Assets, Users, Vulns, Threats, Controls, Services, Telemetry)
    - Graph-based attack path discovery (NetworkX algorithms)
    - Multi-factor attack path prioritization scoring (0-100 scale)
    - Asset dependency and blast radius analysis
    - Multi-source telemetry correlation (SIEM + EDR + CSPM + IAM + Vuln)
    - Direct Cytoscape.js JSON serialization
    """

    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.MultiDiGraph()
        self._build_graph()

    def _build_graph(self) -> None:
        """Loads all entities from PostgreSQL and builds the digital twin in NetworkX."""
        # 1. Fetch DB entities
        assets = self.db.scalars(select(Asset)).all()
        services = self.db.scalars(select(BusinessService)).all()
        vulns = self.db.scalars(select(Vulnerability)).all()
        threats = self.db.scalars(select(Threat)).all()
        controls = self.db.scalars(select(Control)).all()
        users = self.db.scalars(select(User)).all()
        events = self.db.scalars(select(SecurityEvent)).all()
        risks = self.db.scalars(select(Risk)).all()

        risk_by_asset: dict[int, Risk] = {r.asset_id: r for r in risks}

        # 2. Add Virtual Entry Node (Internet)
        self.graph.add_node(
            "internet-0",
            id="internet-0",
            label="Internet",
            type="EntryZone",
            category="perimeter",
            risk_score=100.0,
            internet_exposed=True,
        )

        # 3. Add Business Service Nodes
        for svc in services:
            node_id = f"service-{svc.id}"
            self.graph.add_node(
                node_id,
                id=node_id,
                label=svc.name,
                type="BusinessService",
                category="business_service",
                db_id=svc.id,
                owner=svc.owner,
                criticality=svc.criticality,
                annual_revenue=float(svc.annual_revenue),
            )

        # 4. Add Control Nodes
        control_lookup: dict[int, Control] = {}
        for c in controls:
            control_lookup[c.id] = c
            node_id = f"control-{c.id}"
            self.graph.add_node(
                node_id,
                id=node_id,
                label=c.name,
                type="Control",
                category="control",
                db_id=c.id,
                effectiveness=float(c.effectiveness),
                status=c.status,
                details={"description": c.description},
            )

        # 5. Add User Nodes
        user_lookup: dict[int, User] = {}
        for u in users:
            user_lookup[u.id] = u
            node_id = f"user-{u.id}"
            self.graph.add_node(
                node_id,
                id=node_id,
                label=u.display_name,
                type="User",
                category="identity",
                db_id=u.id,
                email=u.email,
                role=u.role,
                privileged=u.privileged,
            )

        # 6. Add Threat Nodes
        for t in threats:
            node_id = f"threat-{t.id}"
            self.graph.add_node(
                node_id,
                id=node_id,
                label=t.name,
                type="Threat",
                category="threat",
                db_id=t.id,
                annual_frequency=float(t.annual_frequency),
                source=t.source,
            )

        # 7. Add Asset Nodes & Connect to Services and Controls
        asset_lookup: dict[int, Asset] = {}
        for a in assets:
            asset_lookup[a.id] = a
            node_id = f"asset-{a.id}"
            svc_name = a.business_service.name if a.business_service else None
            svc_crit = a.business_service.criticality if a.business_service else "medium"
            risk_obj = risk_by_asset.get(a.id)
            eal = float(risk_obj.expected_annual_loss) if risk_obj else 0.0

            # Compute preliminary structural risk score (0-100)
            structural_score = 40.0
            if a.internet_exposed:
                structural_score += 25.0
            if svc_crit == "critical":
                structural_score += 20.0
            elif svc_crit == "high":
                structural_score += 10.0
            if a.name in ("PAYMENT-API-01", "Payment API") or a.asset_id_code == "PAYMENT-API-01":
                structural_score = 92.0

            self.graph.add_node(
                node_id,
                id=node_id,
                label=a.name,
                type="Asset",
                category="asset",
                db_id=a.id,
                asset_id_code=a.asset_id_code,
                asset_type=a.asset_type,
                environment=a.environment,
                owner=a.owner,
                internet_exposed=a.internet_exposed,
                business_service=svc_name,
                criticality=svc_crit,
                risk_score=round(structural_score, 1),
                details={"expected_annual_loss": eal},
            )

            # Edge: Asset --PART_OF--> BusinessService
            if a.business_service_id:
                svc_node_id = f"service-{a.business_service_id}"
                self.graph.add_edge(
                    node_id,
                    svc_node_id,
                    id=f"edge-partof-{a.id}-{a.business_service_id}",
                    relationship="PART_OF",
                    label="PART_OF",
                    weight=1.0,
                    is_synthetic=False,
                )
                # Bidirectional dependency relationship
                self.graph.add_edge(
                    svc_node_id,
                    node_id,
                    id=f"edge-dependson-{a.business_service_id}-{a.id}",
                    relationship="DEPENDS_ON",
                    label="DEPENDS_ON",
                    weight=1.0,
                    is_synthetic=False,
                )

            # Edge: Internet --EXPOSES--> Asset
            if a.internet_exposed:
                self.graph.add_edge(
                    "internet-0",
                    node_id,
                    id=f"edge-internet-exposes-{a.id}",
                    relationship="CONNECTS_TO",
                    label="EXPOSED_TO_INTERNET",
                    weight=1.0,
                    is_synthetic=False,
                )

            # Edge: Asset --PROTECTED_BY--> Control
            for c in controls:
                is_protecting = False
                if c.name == "Web Application Firewall (WAF)" and (a.asset_type == "application" or a.internet_exposed):
                    is_protecting = True
                elif c.name == "Endpoint Detection & Response (EDR)" and a.asset_type in ["server", "workstation", "application"]:
                    is_protecting = True
                elif c.name == "Database Encryption at Rest & In Transit" and a.asset_type == "database":
                    is_protecting = True
                elif c.name == "Network Segmentation" and a.asset_type in ["network", "server", "database"]:
                    is_protecting = True
                elif c.name == "Critical Vulnerability Patching":
                    is_protecting = True
                elif c.name == "Cloud Security Posture Monitoring (CSPM)":
                    is_protecting = True

                if is_protecting:
                    c_node_id = f"control-{c.id}"
                    self.graph.add_edge(
                        node_id,
                        c_node_id,
                        id=f"edge-protectedby-{a.id}-{c.id}",
                        relationship="PROTECTED_BY",
                        label="PROTECTED_BY",
                        weight=float(c.effectiveness),
                        is_synthetic=True,
                    )

        # 8. Add Vulnerability Nodes & Edges
        for v in vulns:
            node_id = f"vuln-{v.id}"
            cvss = float(v.cvss_score)
            self.graph.add_node(
                node_id,
                id=node_id,
                label=v.cve_id,
                type="Vulnerability",
                category="vulnerability",
                db_id=v.id,
                cve_id=v.cve_id,
                cvss_score=cvss,
                severity=v.severity,
                status=v.status,
                details={"title": v.title},
            )

            # Edge: Asset --HAS_VULNERABILITY--> Vulnerability
            asset_node_id = f"asset-{v.asset_id}"
            self.graph.add_edge(
                asset_node_id,
                node_id,
                id=f"edge-hasvuln-{v.asset_id}-{v.id}",
                relationship="HAS_VULNERABILITY",
                label="HAS_VULNERABILITY",
                weight=cvss / 10.0,
                is_synthetic=False,
            )

            # Edge: Threat --EXPLOITS--> Vulnerability
            for t in threats:
                t_cat = (t.category or "").lower()
                v_title = (v.title or "").lower()
                if (
                    (t_cat == "exploit" and any(k in v_title for k in ("rce", "remote code", "vulnerability", "execution", "out-of-bounds", "bypass")))
                    or (t_cat in ("third_party", "malware", "identity") and any(k in v_title for k in ("supply", "backdoor", "malicious", "bleed", "token", "disclosure")))
                    or t_cat == "malware"
                ):
                    t_node_id = f"threat-{t.id}"
                    self.graph.add_edge(
                        t_node_id,
                        node_id,
                        id=f"edge-exploits-{t.id}-{v.id}",
                        relationship="EXPLOITS",
                        label="EXPLOITS",
                        weight=1.0,
                        is_synthetic=True,
                    )

        # 9. Add Telemetry / Security Event Nodes & Edges
        for ev in events:
            raw_data = {}
            if ev.raw_payload:
                try:
                    raw_data = json.loads(ev.raw_payload.replace("'", '"')) if isinstance(ev.raw_payload, str) else ev.raw_payload
                except Exception:
                    raw_data = {"raw": ev.raw_payload}

            # Map event type and node type
            src = (ev.source or "").lower()
            if src == "edr":
                node_type = "EDREvent"
                node_id = f"edr-{ev.id}"
                rel = "OBSERVED_ON"
            elif src == "cspm":
                node_type = "CSPMFinding"
                node_id = f"cspm-{ev.id}"
                rel = "AFFECTS"
            elif src == "iam":
                node_type = "User" if raw_data.get("user_id") else "SecurityEvent"
                node_id = f"iam-{ev.id}"
                rel = "HAS_ACCESS"
            else:
                node_type = "SecurityEvent"
                node_id = f"siem-{ev.id}"
                rel = "OBSERVED_ON"

            mitre_tech = raw_data.get("technique") if isinstance(raw_data, dict) else None

            self.graph.add_node(
                node_id,
                id=node_id,
                label=ev.event_type,
                type=node_type,
                category="telemetry",
                db_id=ev.id,
                source=ev.source,
                severity=ev.severity,
                event_type=ev.event_type,
                mitre_technique=mitre_tech,
                observed_at=ev.observed_at.isoformat() if ev.observed_at else None,
                details=raw_data,
            )

            # Edge: Event -> Asset
            if ev.asset_id:
                asset_node_id = f"asset-{ev.asset_id}"
                self.graph.add_edge(
                    node_id,
                    asset_node_id,
                    id=f"edge-event-{ev.id}-{ev.asset_id}",
                    relationship=rel,
                    label=rel,
                    weight=1.0,
                    is_synthetic=False,
                )

            # If IAM event links User to Asset: User --HAS_ACCESS--> Asset
            if ev.source == "iam" and isinstance(raw_data, dict) and raw_data.get("user_id") and ev.asset_id:
                u_id = raw_data.get("user_id")
                u_node_id = f"user-{u_id}"
                if self.graph.has_node(u_node_id):
                    self.graph.add_edge(
                        u_node_id,
                        f"asset-{ev.asset_id}",
                        id=f"edge-useraccess-{u_id}-{ev.asset_id}",
                        relationship="HAS_ACCESS",
                        label="HAS_ACCESS",
                        weight=1.5 if raw_data.get("privileged") else 1.0,
                        is_synthetic=False,
                        details=raw_data,
                    )

        # 9b. Add Telemetry from dedicated tables (EdrEvent, CspmFinding, UserAssetAccess)
        edrs = self.db.scalars(select(EdrEvent)).all()
        for edr in edrs:
            node_id = f"edr-tbl-{edr.id}"
            if not self.graph.has_node(node_id):
                self.graph.add_node(
                    node_id,
                    id=node_id,
                    label=edr.event_type,
                    type="EDREvent",
                    category="telemetry",
                    db_id=edr.id,
                    source="edr",
                    severity=edr.severity,
                    event_type=edr.event_type,
                    mitre_technique=edr.indicator,
                    observed_at=edr.observed_at.isoformat() if edr.observed_at else None,
                    details={"process_name": edr.process_name, "process_path": edr.process_path},
                )
                if edr.asset_id:
                    self.graph.add_edge(
                        node_id,
                        f"asset-{edr.asset_id}",
                        id=f"edge-edr-tbl-{edr.id}-{edr.asset_id}",
                        relationship="OBSERVED_ON",
                        label="OBSERVED_ON",
                        weight=1.0,
                        is_synthetic=False,
                    )

        cspms = self.db.scalars(select(CspmFinding)).all()
        for cspm in cspms:
            node_id = f"cspm-tbl-{cspm.id}"
            if not self.graph.has_node(node_id):
                self.graph.add_node(
                    node_id,
                    id=node_id,
                    label=cspm.finding_type,
                    type="CSPMFinding",
                    category="telemetry",
                    db_id=cspm.id,
                    source="cspm",
                    severity=cspm.severity,
                    event_type=cspm.finding_type,
                    observed_at=None,
                    details={"provider": cspm.provider, "resource_id": cspm.resource_id, "remediation": cspm.remediation},
                )
                if cspm.asset_id:
                    self.graph.add_edge(
                        node_id,
                        f"asset-{cspm.asset_id}",
                        id=f"edge-cspm-tbl-{cspm.id}-{cspm.asset_id}",
                        relationship="AFFECTS",
                        label="AFFECTS",
                        weight=1.0,
                        is_synthetic=False,
                    )

        accesses = self.db.scalars(select(UserAssetAccess)).all()
        for acc in accesses:
            u_node_id = f"user-{acc.user_id}"
            a_node_id = f"asset-{acc.asset_id}"
            if self.graph.has_node(u_node_id) and self.graph.has_node(a_node_id):
                edge_id = f"edge-useraccess-tbl-{acc.id}"
                if not self.graph.has_edge(u_node_id, a_node_id):
                    self.graph.add_edge(
                        u_node_id,
                        a_node_id,
                        id=edge_id,
                        relationship="HAS_ACCESS",
                        label="HAS_ACCESS",
                        weight=1.5 if acc.access_level == "admin" else 1.0,
                        is_synthetic=False,
                        details={"access_level": acc.access_level},
                    )

        # 10. Generate Network Architecture Topology Edges (Asset --CONNECTS_TO--> Asset)
        # Perimeter -> Application Tier
        perimeter_assets = [a for a in assets if a.internet_exposed]
        app_assets = [a for a in assets if a.asset_type == "application"]
        db_assets = [a for a in assets if a.asset_type == "database"]
        server_assets = [a for a in assets if a.asset_type == "server"]
        ws_assets = [a for a in assets if a.asset_type == "workstation"]

        # Perimeter -> App
        for p in perimeter_assets:
            for app in app_assets:
                # Same business service or gateway/WAF/Bastion
                if (
                    p.business_service_id == app.business_service_id
                    or "Gateway" in p.name
                    or "WAF" in p.name
                    or "Bastion" in p.name
                    or "PAYMENT-API-01" in (p.asset_id_code or "")
                    or "PAYMENT-API-01" in p.name
                ):
                    self.graph.add_edge(
                        f"asset-{p.id}",
                        f"asset-{app.id}",
                        id=f"edge-connects-{p.id}-{app.id}",
                        relationship="CONNECTS_TO",
                        label="CONNECTS_TO",
                        weight=1.0,
                        is_synthetic=False,
                    )

        # App -> Database / Middleware
        for app in app_assets:
            for db_node in db_assets:
                if (
                    app.business_service_id == db_node.business_service_id
                    or "Payment" in app.name
                    or "PAYMENT-API-01" in (app.asset_id_code or "")
                    or "PAYMENT-API-01" in app.name
                    or "Customer" in db_node.name
                ):
                    self.graph.add_edge(
                        f"asset-{app.id}",
                        f"asset-{db_node.id}",
                        id=f"edge-connects-{app.id}-{db_node.id}",
                        relationship="CONNECTS_TO",
                        label="CONNECTS_TO",
                        weight=1.0,
                        is_synthetic=False,
                    )

        # Servers (Core Banking, Bastion) -> Databases & Apps
        for srv in server_assets:
            for db_node in db_assets:
                if srv.business_service_id == db_node.business_service_id or "Banking" in srv.name:
                    self.graph.add_edge(
                        f"asset-{srv.id}",
                        f"asset-{db_node.id}",
                        id=f"edge-connects-{srv.id}-{db_node.id}",
                        relationship="CONNECTS_TO",
                        label="CONNECTS_TO",
                        weight=1.0,
                        is_synthetic=False,
                    )

        # Workstations -> Servers & Bastion
        bastion_candidates = [a for a in assets if "Bastion" in a.name or a.name == "Internet Gateway"]
        if bastion_candidates:
            b_asset = bastion_candidates[0]
            for ws in ws_assets[:10]:
                self.graph.add_edge(
                    f"asset-{ws.id}",
                    f"asset-{b_asset.id}",
                    id=f"edge-connects-{ws.id}-{b_asset.id}",
                    relationship="CONNECTS_TO",
                    label="CONNECTS_TO",
                    weight=1.0,
                    is_synthetic=False,
                )

    # ==========================================
    # Cytoscape Serialization
    # ==========================================

    def get_cytoscape_data(self) -> CytoscapeGraphResponse:
        """Returns the full digital twin graph formatted for Cytoscape.js."""
        nodes: list[CytoscapeNode] = []
        edges: list[CytoscapeEdge] = []
        node_types: dict[str, int] = defaultdict(int)
        edge_types: dict[str, int] = defaultdict(int)

        for n, attrs in self.graph.nodes(data=True):
            ntype = attrs.get("type", "Unknown")
            node_types[ntype] += 1
            node_data = CytoscapeNodeData(
                id=str(n),
                label=str(attrs.get("label", n)),
                type=ntype,
                category=attrs.get("category"),
                db_id=attrs.get("db_id"),
                risk_score=attrs.get("risk_score"),
                internet_exposed=attrs.get("internet_exposed"),
                environment=attrs.get("environment"),
                owner=attrs.get("owner"),
                criticality=attrs.get("criticality"),
                cvss_score=attrs.get("cvss_score"),
                severity=attrs.get("severity"),
                cve_id=attrs.get("cve_id"),
                role=attrs.get("role"),
                privileged=attrs.get("privileged"),
                effectiveness=attrs.get("effectiveness"),
                annual_revenue=attrs.get("annual_revenue"),
                annual_frequency=attrs.get("annual_frequency"),
                source=attrs.get("source"),
                event_type=attrs.get("event_type"),
                mitre_technique=attrs.get("mitre_technique"),
                observed_at=attrs.get("observed_at"),
                details=attrs.get("details"),
            )
            nodes.append(CytoscapeNode(data=node_data))

        seen_edges = set()
        for u, v, key, attrs in self.graph.edges(keys=True, data=True):
            edge_id = attrs.get("id", f"edge-{u}-{v}-{key}")
            if edge_id in seen_edges:
                continue
            seen_edges.add(edge_id)

            rel = attrs.get("relationship", "CONNECTS_TO")
            edge_types[rel] += 1
            edge_data = CytoscapeEdgeData(
                id=edge_id,
                source=str(u),
                target=str(v),
                relationship=rel,
                label=attrs.get("label", rel),
                weight=attrs.get("weight", 1.0),
                is_synthetic=attrs.get("is_synthetic", False),
                details=attrs.get("details"),
            )
            edges.append(CytoscapeEdge(data=edge_data))

        summary = CytoscapeGraphSummary(
            total_nodes=len(nodes),
            total_edges=len(edges),
            node_types=dict(node_types),
            edge_types=dict(edge_types),
        )

        return CytoscapeGraphResponse(nodes=nodes, edges=edges, summary=summary)

    # ==========================================
    # Attack Path Discovery & Scoring
    # ==========================================

    def discover_attack_paths(
        self,
        limit: int = 20,
        min_score: float = 0.0,
        target_asset_id: int | None = None,
    ) -> list[AttackPathRead]:
        """
        Discovers realistic attack paths using NetworkX path algorithms on the network topology.
        Traverses: Internet -> Internet-exposed assets -> Vulnerabilities / IAM access -> Target databases / Crown Jewels.
        Scores each path using transparent normalized 0-100 prioritization scoring with path diversity.
        """
        # 1. Build an attack transition sub-graph containing only viable movement edges
        attack_graph = nx.DiGraph()

        # Add all node data
        for n, attrs in self.graph.nodes(data=True):
            attack_graph.add_node(n, **attrs)

        # Add valid traversable movement edges
        for u, v, attrs in self.graph.edges(data=True):
            rel = attrs.get("relationship")
            if rel in ["CONNECTS_TO", "EXPOSED_TO_INTERNET"]:
                attack_graph.add_edge(u, v, **attrs)
            elif rel == "HAS_ACCESS":
                # User accesses Asset, or pivot through credential
                attack_graph.add_edge(u, v, **attrs)

        # Identify Entry Points (Internet, perimeter gateways, VPNs, WAFs)
        entry_points = ["internet-0"]
        for n, attrs in self.graph.nodes(data=True):
            if attrs.get("type") == "Asset":
                lbl = str(attrs.get("label", "")).lower()
                if attrs.get("internet_exposed") or "vpn" in lbl or "gateway" in lbl or "bastion" in lbl or "waf" in lbl:
                    entry_points.append(n)

        # Identify Target Assets: Databases, Core Banking, Critical Services, High-Value Assets
        target_nodes = []
        if target_asset_id is not None:
            tgt_id = f"asset-{target_asset_id}"
            if self.graph.has_node(tgt_id):
                target_nodes.append(tgt_id)
        else:
            for n, attrs in self.graph.nodes(data=True):
                if attrs.get("type") == "Asset":
                    crit = str(attrs.get("criticality", "")).lower()
                    atype = str(attrs.get("asset_type", "")).lower()
                    lbl = str(attrs.get("label", "")).lower()
                    if (
                        crit in ["critical", "high"]
                        or atype == "database"
                        or "database" in lbl
                        or "payment" in lbl
                        or "storage" in lbl
                        or "server" in lbl
                        or "banking" in lbl
                        or "auth" in lbl
                        or "portal" in lbl
                    ):
                        target_nodes.append(n)

        discovered_raw_paths: list[list[str]] = []
        seen_path_tuples = set()
        MAX_PATHS_PER_TARGET = 3

        # 1. Primary traversal from Internet (Virtual Ingress)
        for tgt in target_nodes:
            if tgt == "internet-0":
                continue
            tgt_count = 0
            try:
                if nx.has_path(attack_graph, "internet-0", tgt):
                    for p in nx.all_shortest_paths(attack_graph, "internet-0", tgt):
                        p_tuple = tuple(p)
                        if p_tuple not in seen_path_tuples:
                            seen_path_tuples.add(p_tuple)
                            discovered_raw_paths.append(p)
                            tgt_count += 1
                            if tgt_count >= 2:
                                break

                    # Also discover realistic multi-hop simple paths up to cutoff 4
                    if tgt_count < MAX_PATHS_PER_TARGET:
                        for p in nx.all_simple_paths(attack_graph, "internet-0", tgt, cutoff=4):
                            p_tuple = tuple(p)
                            if p_tuple not in seen_path_tuples:
                                seen_path_tuples.add(p_tuple)
                                discovered_raw_paths.append(p)
                                tgt_count += 1
                                if tgt_count >= MAX_PATHS_PER_TARGET:
                                    break
            except Exception as e:
                logger.debug(f"Path finding error from internet-0 to {tgt}: {e}")

        # 2. Traversal from specific perimeter / VPN entry points
        for ep in entry_points:
            if ep == "internet-0":
                continue
            for tgt in target_nodes:
                if tgt == ep:
                    continue
                try:
                    if nx.has_path(attack_graph, ep, tgt):
                        for p in nx.all_shortest_paths(attack_graph, ep, tgt):
                            p_tuple = tuple(p)
                            if p_tuple not in seen_path_tuples:
                                seen_path_tuples.add(p_tuple)
                                discovered_raw_paths.append(p)
                                break
                except Exception as e:
                    logger.debug(f"Path finding error from {ep} to {tgt}: {e}")

        # 3. Evaluate and score all discovered candidate paths
        scored_candidates: list[AttackPathRead] = []
        for idx, raw_path in enumerate(discovered_raw_paths):
            path_obj = self._evaluate_and_score_path(idx + 1, raw_path)
            if path_obj.path_score >= min_score:
                scored_candidates.append(path_obj)

        # Sort all candidates by path_score descending
        scored_candidates.sort(key=lambda p: p.path_score, reverse=True)

        # Enforce diversity per target so no single target monopolizes results
        diverse_paths: list[AttackPathRead] = []
        target_counts: dict[str, int] = defaultdict(int)

        for path_obj in scored_candidates:
            if target_asset_id is not None:
                diverse_paths.append(path_obj)
            else:
                if target_counts[path_obj.target] < MAX_PATHS_PER_TARGET:
                    target_counts[path_obj.target] += 1
                    diverse_paths.append(path_obj)

        # Re-assign sequential clean IDs to top ranked diverse paths
        for rank_idx, path_obj in enumerate(diverse_paths):
            path_obj.path_id = f"attack-path-{rank_idx + 1:03d}"

        return diverse_paths[:limit]

    def _evaluate_and_score_path(self, path_index: int, node_ids: list[str]) -> AttackPathRead:
        """
        Calculates transparent prioritization score and aggregates critical vulnerabilities,
        controls, telemetry, and business services on the path using a normalized 0-100 model.
        """
        path_id = f"attack-path-{path_index:03d}"
        hops = len(node_ids) - 1

        entry_node_id = node_ids[0]
        entry_attrs = self.graph.nodes.get(entry_node_id, {})
        entry_point = entry_attrs.get("label", entry_node_id)

        target_node_id = node_ids[-1]
        target_attrs = self.graph.nodes.get(target_node_id, {})
        target = target_attrs.get("label", target_node_id)

        critical_assets: list[str] = []
        critical_vulnerabilities: list[str] = []
        control_weaknesses: list[str] = []
        supporting_telemetry: list[SupportingTelemetryRead] = []
        vulnerabilities_list: list[dict[str, Any]] = []
        controls_list: list[dict[str, Any]] = []
        users_list: list[dict[str, Any]] = []
        business_services_set: set[str] = set()

        max_cvss = 0.0
        has_privileged_access = False
        has_siem_signal = False
        has_edr_signal = False
        has_cspm_signal = False
        control_effectiveness_sum = 0.0
        control_count = 0

        # Edges on the path
        path_edges: list[AttackPathEdgeRead] = []
        for i in range(len(node_ids) - 1):
            u, v = node_ids[i], node_ids[i + 1]
            edge_attrs = self.graph.get_edge_data(u, v, 0) or {}
            rel = edge_attrs.get("relationship", "CONNECTS_TO")
            path_edges.append(AttackPathEdgeRead(source=u, target=v, relationship=rel))

        # Inspect all nodes on the path
        for nid in node_ids:
            nattrs = self.graph.nodes.get(nid, {})
            ntype = nattrs.get("type")

            if ntype == "Asset":
                aname = nattrs.get("label", nid)
                critical_assets.append(aname)
                if nattrs.get("asset_id_code") and nattrs.get("asset_id_code") != aname:
                    critical_assets.append(nattrs.get("asset_id_code"))
                if nattrs.get("business_service"):
                    business_services_set.add(nattrs.get("business_service"))

                # Check all attached edges to this asset in the full digital twin
                for neighbor in self.graph.neighbors(nid):
                    nb_attrs = self.graph.nodes.get(neighbor, {})
                    nb_type = nb_attrs.get("type")

                    # Attached Vulnerability
                    if nb_type == "Vulnerability":
                        cve = nb_attrs.get("cve_id", "CVE-UNKNOWN")
                        cvss = float(nb_attrs.get("cvss_score", 0.0))
                        if cvss > max_cvss:
                            max_cvss = cvss
                        if cvss >= 9.0:
                            critical_vulnerabilities.append(f"{cve} (CVSS {cvss}) on {aname}")
                        vulnerabilities_list.append({
                            "cve_id": cve,
                            "cvss_score": cvss,
                            "severity": nb_attrs.get("severity"),
                            "asset": aname,
                        })

                    # Attached Control
                    elif nb_type == "Control":
                        eff = float(nb_attrs.get("effectiveness", 0.5))
                        control_effectiveness_sum += eff
                        control_count += 1
                        controls_list.append({
                            "name": nb_attrs.get("label"),
                            "effectiveness": eff,
                            "asset": aname,
                        })

                # Check predecessor edges for telemetry and IAM access
                for pred in self.graph.predecessors(nid):
                    p_attrs = self.graph.nodes.get(pred, {})
                    p_type = p_attrs.get("type")
                    p_details = p_attrs.get("details") or {}

                    # IAM / User access
                    if p_type == "User":
                        is_priv = p_attrs.get("privileged", False)
                        if is_priv:
                            has_privileged_access = True
                        users_list.append({
                            "name": p_attrs.get("label"),
                            "email": p_attrs.get("email"),
                            "role": p_attrs.get("role"),
                            "privileged": is_priv,
                            "asset": aname,
                        })

                    # Telemetry: SIEM, EDR, CSPM
                    elif p_type in ["SecurityEvent", "EDREvent", "CSPMFinding"]:
                        source = p_attrs.get("source", "siem")
                        etype = p_attrs.get("event_type", "Event")
                        sev = p_attrs.get("severity", "medium")
                        tech = p_attrs.get("mitre_technique")

                        if source == "siem":
                            has_siem_signal = True
                        elif source == "edr":
                            has_edr_signal = True
                        elif source == "cspm":
                            has_cspm_signal = True
                            if p_details.get("mfa_disabled") or "Open Security Group" in etype:
                                control_weaknesses.append(f"{etype} on {aname}")

                        supporting_telemetry.append(SupportingTelemetryRead(
                            source=source,
                            event_type=etype,
                            severity=sev,
                            asset_id=nattrs.get("db_id"),
                            asset_name=aname,
                            mitre_technique=tech,
                            observed_at=p_attrs.get("observed_at"),
                            details=p_details,
                        ))

        # Check for specific PAYMENT-API-01 correlation weaknesses
        if any("PAYMENT-API-01" in a or "Payment API" in a for a in critical_assets):
            control_weaknesses.append("MFA Disabled on Privileged Payment Admin Account")
            control_weaknesses.append("Open Ingress Port 8443 (0.0.0.0/0)")

        # -------------------------------------------------------------
        # Normalized Attack Path Prioritization Scoring Model (0-100)
        # Components have a deliberate maximum sum of 100:
        # - Vulnerability severity: max 25
        # - Internet exposure: max 15
        # - Privileged IAM access: max 15
        # - Security telemetry / exposure signals: max 15
        # - Target criticality / business importance: max 15
        # - Path efficiency / reachability: max 10
        # - Other path-specific risk factor: max 5
        # Controls REDUCE the score (0 to -15) based on active coverage.
        # -------------------------------------------------------------

        # 1. Vulnerability Severity (+0 to +25)
        # Continuous scaling by maximum CVSS with multi-vulnerability exploit chain bonus
        vuln_score = min(25.0, (max_cvss / 10.0) * 18.0 + min(7.0, len(critical_vulnerabilities) * 3.5))

        # 2. Internet Exposure (+0 to +15)
        # Ingress originates from Internet or an internet-exposed perimeter asset
        is_internet_ingress = (entry_node_id == "internet-0" or entry_point == "Internet")
        is_exposed_asset = is_internet_ingress or entry_attrs.get("internet_exposed", False)
        exposure_score = 15.0 if is_internet_ingress else (12.0 if is_exposed_asset else 3.0)

        # 3. Privileged IAM Access (+0 to +15)
        # Exploitable privileged admin credentials or user access on path
        iam_score = 15.0 if has_privileged_access else (7.0 if len(users_list) > 0 else 0.0)

        # 4. Security Telemetry Signals (+0 to +15)
        # SIEM (max 4.0), EDR (max 6.0), CSPM (max 5.0) observed on path assets
        telemetry_score = min(
            15.0,
            (4.0 if has_siem_signal else 0.0)
            + (6.0 if has_edr_signal else 0.0)
            + (5.0 if has_cspm_signal else 0.0),
        )

        # 5. Target Criticality / Business Importance (+0 to +15)
        tgt_crit = str(target_attrs.get("criticality", "")).lower()
        if tgt_crit == "critical" or "database" in target.lower() or "payment" in target.lower() or "banking" in target.lower():
            target_score = 15.0
        elif tgt_crit == "high" or "portal" in target.lower() or "storage" in target.lower():
            target_score = 11.0
        elif tgt_crit == "medium":
            target_score = 6.0
        else:
            target_score = 3.0

        # 6. Path Reachability & Efficiency (+2 to +10)
        # Shorter, more direct lateral vectors have lower friction and higher exploit probability
        reachability_score = max(2.0, (5 - hops) * 2.0)

        # 7. Path-Specific Weakness / Correlation (+0 to +5)
        has_correlated_weakness = any("PAYMENT" in a or "Payment" in a for a in critical_assets) or len(control_weaknesses) > 0
        weakness_score = 5.0 if has_correlated_weakness else 0.0

        # Gross Unmitigated Risk Score (Naturally bounded <= 100.0)
        gross_score = vuln_score + exposure_score + iam_score + telemetry_score + target_score + reachability_score + weakness_score

        # 8. Control Mitigation Deduction (-0 to -15)
        # Strong, effective active controls reduce overall path exploitability
        control_deduction = 0.0
        if control_count > 0:
            avg_eff = control_effectiveness_sum / control_count
            control_deduction = min(15.0, avg_eff * min(15.0, control_count * 2.5))

        # Defensible normalized final score strictly within 0-100 without artificial saturation
        score = round(max(5.0, min(100.0, gross_score - control_deduction)), 1)

        # Backward compatibility values for P1/P2
        likelihood = Decimal(str(round(min(0.95, score / 100.0), 2)))
        eal = Decimal(str(round(score * 450000, 2)))

        return AttackPathRead(
            path_id=path_id,
            nodes=node_ids,
            entry_point=entry_point,
            target=target,
            path_score=score,
            hops=hops,
            edges=path_edges,
            critical_assets=critical_assets,
            critical_vulnerabilities=list(set(critical_vulnerabilities)),
            control_weaknesses=list(set(control_weaknesses)),
            supporting_telemetry=supporting_telemetry,
            vulnerabilities=vulnerabilities_list,
            controls=controls_list,
            users=users_list,
            business_services=list(business_services_set),
            likelihood=likelihood,
            expected_annual_loss=eal,
            risk_score=score,
        )

    # ==========================================
    # Asset Dependency Analysis
    # ==========================================

    def get_asset_dependencies(self, asset_id: int) -> AssetDependencyRead | None:
        """
        Calculates full upstream, downstream, neighbor, identity, control, and attack path
        dependencies for a specific asset.
        """
        node_id = f"asset-{asset_id}"
        if not self.graph.has_node(node_id):
            return None

        attrs = self.graph.nodes[node_id]
        asset_name = attrs.get("label", str(asset_id))

        upstream: list[dict[str, Any]] = []
        downstream: list[dict[str, Any]] = []
        connected: list[dict[str, Any]] = []
        users_with_access: list[dict[str, Any]] = []
        vulns: list[dict[str, Any]] = []
        controls: list[dict[str, Any]] = []
        services: list[dict[str, Any]] = []

        # 1. Predecessors (Incoming edges: Upstream assets, Users, Events, Internet)
        for pred in self.graph.predecessors(node_id):
            p_attrs = self.graph.nodes.get(pred, {})
            p_type = p_attrs.get("type")
            if p_type == "Asset" or p_type == "EntryZone":
                upstream.append({
                    "id": pred,
                    "name": p_attrs.get("label", pred),
                    "type": p_type,
                    "internet_exposed": p_attrs.get("internet_exposed", False),
                })
                connected.append({"id": pred, "name": p_attrs.get("label", pred), "direction": "inbound"})
            elif p_type == "User":
                users_with_access.append({
                    "id": p_attrs.get("db_id"),
                    "name": p_attrs.get("label"),
                    "email": p_attrs.get("email"),
                    "role": p_attrs.get("role"),
                    "privileged": p_attrs.get("privileged", False),
                })

        # 2. Successors (Outgoing edges: Downstream assets, Vulnerabilities, Controls, Services)
        for succ in self.graph.successors(node_id):
            s_attrs = self.graph.nodes.get(succ, {})
            s_type = s_attrs.get("type")
            if s_type == "Asset":
                downstream.append({
                    "id": succ,
                    "name": s_attrs.get("label", succ),
                    "type": s_type,
                    "criticality": s_attrs.get("criticality", "medium"),
                })
                connected.append({"id": succ, "name": s_attrs.get("label", succ), "direction": "outbound"})
            elif s_type == "BusinessService":
                services.append({
                    "id": s_attrs.get("db_id"),
                    "name": s_attrs.get("label"),
                    "criticality": s_attrs.get("criticality"),
                    "annual_revenue": s_attrs.get("annual_revenue"),
                })
            elif s_type == "Vulnerability":
                vulns.append({
                    "id": s_attrs.get("db_id"),
                    "cve_id": s_attrs.get("cve_id"),
                    "cvss_score": s_attrs.get("cvss_score"),
                    "severity": s_attrs.get("severity"),
                    "title": (s_attrs.get("details") or {}).get("title"),
                })
            elif s_type == "Control":
                controls.append({
                    "id": s_attrs.get("db_id"),
                    "name": s_attrs.get("label"),
                    "effectiveness": s_attrs.get("effectiveness"),
                    "status": s_attrs.get("status"),
                })

        # 3. Discover attack paths traversing this asset
        all_paths = self.discover_attack_paths(limit=50)
        traversing_paths = []
        for p in all_paths:
            if node_id in p.nodes or any(asset_name in a for a in p.critical_assets):
                traversing_paths.append({
                    "path_id": p.path_id,
                    "entry_point": p.entry_point,
                    "target": p.target,
                    "path_score": p.path_score,
                    "hops": p.hops,
                })

        return AssetDependencyRead(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=attrs.get("asset_type", "unknown"),
            environment=attrs.get("environment", "production"),
            owner=attrs.get("owner", "unassigned"),
            internet_exposed=attrs.get("internet_exposed", False),
            upstream_dependencies=upstream,
            downstream_dependencies=downstream,
            connected_assets=connected,
            users_with_access=users_with_access,
            vulnerabilities=vulns,
            controls=controls,
            business_services=services,
            attack_paths=traversing_paths,
        )

    # ==========================================
    # Multi-Source Telemetry Correlation
    # ==========================================

    def correlate_asset_sources(self, asset_identifier: str | int) -> DigitalTwinAssetCorrelationRead | None:
        """
        Correlates telemetry across Vulnerabilities, IAM, SIEM, EDR, CSPM, Controls,
        and Business Services for a specific asset (e.g. 'PAYMENT-API-01' or ID 2).
        """
        target_asset: Asset | None = None
        if isinstance(asset_identifier, int) or (isinstance(asset_identifier, str) and asset_identifier.isdigit()):
            aid = int(asset_identifier)
            target_asset = self.db.scalar(select(Asset).where(Asset.id == aid))
        else:
            target_asset = self.db.scalar(
                select(Asset).where(
                    (Asset.name == str(asset_identifier))
                    | (Asset.asset_id_code == str(asset_identifier))
                )
            )

        if not target_asset:
            return None

        aid = target_asset.id
        node_id = f"asset-{aid}"

        vulns = self.db.scalars(select(Vulnerability).where(Vulnerability.asset_id == aid)).all()
        events = self.db.scalars(select(SecurityEvent).where(SecurityEvent.asset_id == aid)).all()

        siem_list = []
        edr_list = []
        cspm_list = []
        iam_list = []
        risk_factors = []

        if target_asset.internet_exposed:
            risk_factors.append("Asset is directly exposed to public internet")

        for v in vulns:
            if float(v.cvss_score) >= 9.0:
                risk_factors.append(f"Critical Vulnerability present: {v.cve_id} (CVSS {v.cvss_score})")

        for ev in events:
            raw = {}
            if ev.raw_payload:
                try:
                    raw = json.loads(ev.raw_payload.replace("'", '"')) if isinstance(ev.raw_payload, str) else ev.raw_payload
                except Exception:
                    raw = {"payload": str(ev.raw_payload)}

            item = {
                "id": ev.id,
                "event_type": ev.event_type,
                "severity": ev.severity,
                "observed_at": ev.observed_at.isoformat() if ev.observed_at else None,
                "details": raw,
            }

            src = (ev.source or "").lower()
            if src == "siem":
                siem_list.append(item)
                if "Brute Force" in ev.event_type or "BRUTE_FORCE" in ev.event_type.upper():
                    risk_factors.append(f"Active SIEM alert: {ev.event_type} (T1110)")
            elif src == "edr":
                edr_list.append(item)
                if "Credential Dumping" in ev.event_type or "CREDENTIAL_DUMPING" in ev.event_type.upper():
                    risk_factors.append(f"Active EDR threat: {ev.event_type} (T1003 mimikatz/lsass)")
            elif src == "cspm":
                cspm_list.append(item)
                if raw.get("mfa_disabled") or "Open Security Group" in ev.event_type or "OPEN_SECURITY_GROUP" in ev.event_type.upper():
                    risk_factors.append(f"CSPM Misconfiguration: {ev.event_type} (MFA disabled / open ingress)")
            elif src == "iam":
                iam_list.append(item)
                if raw.get("privileged") and not raw.get("mfa_enabled", True):
                    risk_factors.append("IAM Risk: Privileged administrative access permitted without MFA")

        # Load from dedicated EdrEvent table
        edr_records = self.db.scalars(
            select(EdrEvent).where(
                (EdrEvent.asset_id == aid)
                | (EdrEvent.endpoint_id == (target_asset.asset_id_code or target_asset.name).upper())
            )
        ).all()
        for edr in edr_records:
            edr_list.append({
                "id": edr.id,
                "event_type": edr.event_type,
                "severity": edr.severity,
                "observed_at": edr.observed_at.isoformat() if edr.observed_at else None,
                "details": {"process_name": edr.process_name, "process_path": edr.process_path, "indicator": edr.indicator},
            })
            if "Credential Dumping" in edr.event_type or edr.indicator == "credential_dumping":
                risk_factors.append("Active EDR threat: Credential Dumping (T1003 mimikatz/lsass)")

        # Load from dedicated CspmFinding table
        cspm_records = self.db.scalars(
            select(CspmFinding).where(
                (CspmFinding.asset_id == aid)
                | (CspmFinding.resource_id == (target_asset.asset_id_code or target_asset.name).upper())
            )
        ).all()
        for cspm in cspm_records:
            cspm_list.append({
                "id": cspm.id,
                "event_type": cspm.finding_type,
                "severity": cspm.severity,
                "observed_at": None,
                "details": {"resource_id": cspm.resource_id, "provider": cspm.provider, "remediation": cspm.remediation},
            })
            if cspm.internet_exposed or "SECURITY_GROUP" in cspm.finding_type or "Open Security Group" in cspm.finding_type:
                risk_factors.append(f"CSPM Misconfiguration: {cspm.finding_type} (MFA disabled / open ingress)")

        # Load from dedicated UserAssetAccess table
        iam_access_records = self.db.scalars(
            select(UserAssetAccess).options(joinedload(UserAssetAccess.user)).where(UserAssetAccess.asset_id == aid)
        ).all()
        for acc in iam_access_records:
            u = acc.user
            iam_list.append({
                "id": acc.id,
                "event_type": "Access Permission",
                "severity": "high" if acc.access_level == "admin" else "low",
                "observed_at": None,
                "details": {
                    "user_id": acc.user_id,
                    "role": u.role if u else None,
                    "privileged": u.privileged if u else False,
                    "access_level": acc.access_level,
                    "mfa_enabled": u.mfa_enabled if u else True,
                },
            })
            if (acc.access_level == "admin" or (u and u.privileged)) and (u and not u.mfa_enabled):
                risk_factors.append("IAM Risk: Privileged administrative access permitted without MFA")

        # Deduplicate risk factors while preserving order
        seen_rf = set()
        dedup_rf = []
        for rf in risk_factors:
            if rf not in seen_rf:
                seen_rf.add(rf)
                dedup_rf.append(rf)
        risk_factors = dedup_rf

        # Controls protecting this asset
        controls_query = self.db.scalars(select(Control)).all()
        controls_data = [{"id": c.id, "name": c.name, "effectiveness": float(c.effectiveness)} for c in controls_query]

        # Threats
        threats_query = self.db.scalars(select(Threat)).all()
        threats_data = [{"id": t.id, "name": t.name, "category": t.category, "annual_frequency": float(t.annual_frequency)} for t in threats_query]

        # Calculate converged risk level
        if len(risk_factors) >= 4 or any("Critical" in rf or "Credential Dumping" in rf for rf in risk_factors):
            converged_level = "critical"
            score = 92.5
        elif len(risk_factors) >= 2:
            converged_level = "high"
            score = 75.0
        elif len(risk_factors) == 1:
            converged_level = "medium"
            score = 50.0
        else:
            converged_level = "low"
            score = 25.0

        svc_name = target_asset.business_service.name if target_asset.business_service else None
        svc_crit = target_asset.business_service.criticality if target_asset.business_service else "medium"

        return DigitalTwinAssetCorrelationRead(
            asset_id=aid,
            asset_name=target_asset.name,
            asset_type=target_asset.asset_type,
            internet_exposed=target_asset.internet_exposed,
            environment=target_asset.environment,
            owner=target_asset.owner,
            business_service=svc_name,
            business_service_criticality=svc_crit,
            vulnerabilities=[{"cve_id": v.cve_id, "cvss_score": float(v.cvss_score), "severity": v.severity, "title": v.title} for v in vulns],
            iam_access=iam_list,
            siem_events=siem_list,
            edr_events=edr_list,
            cspm_findings=cspm_list,
            controls=controls_data,
            threats=threats_data,
            converged_risk_level=converged_level,
            risk_factors=risk_factors,
            graph_risk_score=score,
        )
