"""
P3 Attack Path & Graph Engine Data Models.
Upstream contract for attack paths, graph relationships, dependencies,
critical assets, business services, and choke points.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class GraphNode:
    node_id: str
    label: str
    node_type: str  # "EXTERNAL_THREAT", "ASSET", "IAM_ACCOUNT", "VULNERABILITY", "BUSINESS_SERVICE", "DATA_STORE"
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    relationship: str  # "EXPLOITS", "AUTHENTICATES_TO", "COMMUNICATES_WITH", "SUPPORTS", "STORES_DATA_FOR"
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttackPathStep:
    step_number: int
    from_entity: str
    to_entity: str
    action_type: str  # "EXPLOIT_VULNERABILITY", "CREDENTIAL_ABUSE", "LATERAL_MOVEMENT", "DATA_EXFILTRATION"
    technique_id: str  # MITRE ATT&CK ID e.g. "T1190", "T1003", "T1021.002", "T1048"
    description: str
    choke_point: bool = False
    remediation_control: Optional[str] = None


@dataclass
class AttackPath:
    path_id: str
    name: str
    source_threat: str
    target_business_service: str
    target_critical_asset: str
    traversal_probability: float  # 0.0 to 1.0
    estimated_financial_loss: float  # In USD
    steps: List[AttackPathStep]
    choke_points: List[str]
    active_threat_indicators: List[str] = field(default_factory=list)


@dataclass
class BusinessService:
    service_id: str
    name: str
    tier: str
    description: str
    dependent_asset_ids: List[str]
    maximum_tolerable_downtime_hours: int
    financial_loss_per_hour_downtime: float
