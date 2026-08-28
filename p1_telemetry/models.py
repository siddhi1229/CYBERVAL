"""
P1 Telemetry & Asset Data Models.
Upstream contract for assets, vulnerabilities, IAM, SIEM, EDR, CSPM, and Threat Intelligence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AssetCriticality(str, Enum):
    TIER_1 = "Tier 1 - Mission Critical"
    TIER_2 = "Tier 2 - Business Critical"
    TIER_3 = "Tier 3 - Operational"
    TIER_4 = "Tier 4 - Non-Critical"


@dataclass
class Asset:
    id: str
    name: str
    asset_type: str  # e.g., "API Gateway", "Database", "Microservice", "K8s Cluster"
    criticality: AssetCriticality
    business_service: str  # e.g., "Payment Processing", "Customer Portal", "Data Analytics"
    internet_exposed: bool
    ip_address: str
    cloud_provider: str
    tags: Dict[str, str] = field(default_factory=dict)
    owner: str = "Engineering"


@dataclass
class Vulnerability:
    cve_id: str
    title: str
    cvss_score: float
    epss_score: float  # 0.0 to 1.0 (Exploit Prediction Scoring System)
    known_exploited: bool  # CISA KEV Catalog listed
    affected_asset_id: str
    discovery_date: str
    age_days: int
    remediation_sla_days: int
    patch_available: bool
    description: str = ""
    attack_vector: str = "NETWORK"


@dataclass
class IAMAccount:
    account_id: str
    username: str
    role: str
    is_privileged: bool
    mfa_enabled: bool
    assigned_assets: List[str] = field(default_factory=list)
    last_login: str = ""
    status: str = "ACTIVE"


@dataclass
class SIEMAlert:
    alert_id: str
    asset_id: str
    alert_type: str  # e.g., "Brute Force", "Anomalous Volume", "Port Scan"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    timestamp: str
    description: str
    source_ip: str
    event_count: int


@dataclass
class EDRTelemetry:
    telemetry_id: str
    asset_id: str
    detection_type: str  # e.g., "Credential Dumping (LSASS)", "Process Injection", "Mimikatz Signature"
    severity: str
    process_name: str
    command_line: str
    timestamp: str
    mitre_technique: str


@dataclass
class CSPMFinding:
    finding_id: str
    asset_id: str
    resource_type: str
    issue: str  # e.g., "Open Security Group (0.0.0.0/0 on port 8443)", "Public Storage Bucket"
    severity: str
    compliance_framework: str
    remediation_guide: str


@dataclass
class ThreatIntelIndicator:
    indicator_id: str
    cve_id: Optional[str]
    threat_actor: str
    campaign: str
    active_in_wild: bool
    targeted_sectors: List[str]
    ransomware_associated: bool
    reported_date: str
