"""
CYBERVAL - Module P5: Investment Optimization
Mock Data Fixtures for Upstream Modules (P2: Risk Engine & P3: Digital Twin Graph)

This module provides mock baseline Expected Annual Loss (EAL) values and candidate
security controls to allow P5 to run completely standalone during development.
All monetary amounts are in Indian Rupees (INR - ₹).
"""

from typing import Dict, List, Any

# ==============================================================================
# UPSTREAM P2 & P3 MOCK DATA: BASELINE EXPECTED ANNUAL LOSS (EAL)
# ==============================================================================

# Total Enterprise Baseline Expected Annual Loss (EAL) = ₹10,00,00,000 (₹10 Crores)
MOCK_P2_ENTERPRISE_BASELINE_EAL: float = 100_000_000.0

# Asset-Level Baseline EAL from P3 Digital Twin Graph / P2 Asset Risk Breakdown
MOCK_P3_ASSET_BASELINE_EAL: Dict[str, float] = {
    "PAYMENT-API-01": 42_000_000.0,       # ₹4,20,00,000 (₹4.2 Cr) - Critical Payment Gateway
    "WEB-ASSETS-CLUSTER": 30_000_000.0,   # ₹3,00,00,000 (₹3.0 Cr) - Public Web & Edge Servers
    "ENDPOINT-FLEET": 30_000_000.0,       # ₹3,00,00,000 (₹3.0 Cr) - Enterprise Workstations & Laptops
    "CORE-NETWORK-INFRA": 28_000_000.0,   # ₹2,80,00,000 (₹2.8 Cr) - Core Routing & Internal VLANs
    "ENTERPRISE-WIDE": 100_000_000.0,     # ₹10,00,00,000 (₹10.0 Cr) - Enterprise-wide scope
}

# ==============================================================================
# UPSTREAM P1/P2 MOCK DATA: AVAILABLE CANDIDATE SECURITY CONTROLS
# ==============================================================================

MOCK_AVAILABLE_CONTROLS_RAW: List[Dict[str, Any]] = [
    {
        "id": "CTRL-MFA-001",
        "name": "Implement Privileged Identity MFA",
        "description": "FIDO2 / Hardware token multi-factor authentication for privileged API and admin access",
        "annual_cost": 1_500_000.0,  # ₹15,00,000 (₹15 Lakhs)
        "target_asset_or_risk": "PAYMENT-API-01",
        "effectiveness": 0.75,  # 75% risk reduction on Payment API
        "baseline_eal": 42_000_000.0,  # ₹4,20,00,000
    },
    {
        "id": "CTRL-PATCH-002",
        "name": "Patch CVE-2024-21762 & Harden Servers",
        "description": "Critical SSL-VPN / edge server zero-day patch deployment and CIS benchmark hardening",
        "annual_cost": 4_000_000.0,  # ₹40,00,000 (₹40 Lakhs)
        "target_asset_or_risk": "WEB-ASSETS-CLUSTER",
        "effectiveness": 0.60,  # 60% risk reduction across web assets
        "baseline_eal": 30_000_000.0,  # ₹3,00,00,000
    },
    {
        "id": "CTRL-EDR-003",
        "name": "Deploy EDR Advanced Agent",
        "description": "Next-gen Endpoint Detection and Response with automated containment across fleet",
        "annual_cost": 3_000_000.0,  # ₹30,00,000 (₹30 Lakhs)
        "target_asset_or_risk": "ENDPOINT-FLEET",
        "effectiveness": 0.40,  # 40% risk reduction
        "baseline_eal": 30_000_000.0,  # ₹3,00,00,000
    },
    {
        "id": "CTRL-NET-004",
        "name": "Network Micro-segmentation",
        "description": "Zero Trust software-defined micro-segmentation for lateral movement mitigation",
        "annual_cost": 5_000_000.0,  # ₹50,00,000 (₹50 Lakhs)
        "target_asset_or_risk": "CORE-NETWORK-INFRA",
        "effectiveness": 0.50,  # 50% risk reduction
        "baseline_eal": 28_000_000.0,  # ₹2,80,00,000
    }
]


def format_inr(amount: float, symbol: str = "₹") -> str:
    """
    Format a floating-point number into Indian Rupee (INR) representation.
    Example: 10000000 -> ₹1,00,00,000.00 (₹1.00 Cr)
    """
    if amount is None:
        return f"{symbol}0.00"
    
    is_negative = amount < 0
    abs_amount = abs(amount)
    
    int_part = int(abs_amount)
    dec_part = f"{abs_amount - int_part:.2f}"[1:]  # e.g., '.00'
    
    s = str(int_part)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted = ",".join(groups) + "," + last3
        
    sign = "-" if is_negative else ""
    
    if abs_amount >= 10_000_000:
        cr_val = abs_amount / 10_000_000
        return f"{sign}{symbol}{formatted}{dec_part} ({symbol}{cr_val:.2f} Cr)"
    elif abs_amount >= 100_000:
        lakh_val = abs_amount / 100_000
        return f"{sign}{symbol}{formatted}{dec_part} ({symbol}{lakh_val:.2f} Lakh)"
    else:
        return f"{sign}{symbol}{formatted}{dec_part}"
