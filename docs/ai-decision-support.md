# P4 — AI Decision Support Layer Documentation

## Executive Overview

**CYBERVAL P4** is the **Explainable AI Decision Support Layer** designed for Chief Information Security Officers (CISOs), Chief Risk Officers (CROs), and enterprise security leadership. It translates multi-source raw telemetry (P1), quantitative FAIR/Monte Carlo financial risk calculations (P2), and attack path graph relationships (P3) into actionable executive intelligence, ROI-ranked remediation recommendations, and what-if predictive simulations.

```
+-----------------------------------------------------------------------------------+
|                           CYBERVAL PLATFORM ARCHITECTURE                           |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [P1: Telemetry & Ingestion]     [P2: Quantitative Risk Engine]  [P3: Graph Engine] |
|   - Assets (Inventory/Tags)       - Loss Event Frequency (LEF)    - Attack Paths   |
|   - Vulnerabilities (CVE/EPSS)    - Single Loss Expectancy (SLE)  - Choke Points   |
|   - IAM (Privilege/MFA Status)    - Expected Annual Loss (EAL)    - Dependencies   |
|   - SIEM / EDR / CSPM Findings    - 95% / 99% Value at Risk (VaR) - Business Srvs  |
|   - CISA KEV / Threat Intel       - Control Effectiveness Scores                   |
|                  \                       |                       /                 |
|                   \                      |                      /                  |
|                    v                     v                     v                   |
|  +-----------------------------------------------------------------------------+  |
|  |                  P4 — AI DECISION SUPPORT LAYER                             |  |
|  |                                                                             |  |
|  |  [Zero-Hallucination Guardrails] <---> [Multi-Source Evidence Synthesizer] |  |
|  |  [Deterministic Reasoning Engine] <--> [ROI Recommendation Prioritizer]   |  |
|  |  [What-If Simulation Engine]     <---> [Executive Natural Language Parser]  |  |
|  +-----------------------------------------------------------------------------+  |
|                                          |                                         |
|                                          v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                             REST API INTERFACE                              |  |
|  |   POST /api/ai/query    POST /api/ai/recommend    POST /api/simulation/run  |  |
|  +-----------------------------------------------------------------------------+  |
|                                          |                                         |
|                                          v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                        CISO / EXECUTIVE DECISION MAKER                      |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 1. Upstream Data Sources Consumed

P4 acts strictly as an analytical and explainable reasoning layer over existing upstream CYBERVAL services:

| Upstream Layer | Consumed Data Attributes | Role in Decision Support |
| :--- | :--- | :--- |
| **P1: Telemetry & Assets** | • Multi-source asset inventory (ID, criticality tier, public IP, exposure)<br>• Vulnerability registry (CVE-ID, CVSS, EPSS score, CISA KEV status)<br>• Identity & Access Management (Privileged accounts, MFA enablement)<br>• SIEM alerts (Brute force, authentication anomalies)<br>• EDR telemetry (LSASS credential dumping, suspicious child processes)<br>• CSPM misconfigurations (Open Security Groups, S3 public read)<br>• Threat intelligence (Threat actors, campaigns, sector targeting) | Provides factual internal and external threat telemetry used for multi-source evidence assembly. |
| **P2: Quantitative Risk Engine** | • Expected Annual Loss (EAL in USD)<br>• Single Loss Expectancy (SLE) broken down by Business Interruption, Forensics, Legal/Fines, Extortion, Churn<br>• Annual Loss Event Frequency (LEF)<br>• 1-Year 95% and 99% Value at Risk (VaR)<br>• Risk drivers and contribution breakdown ($ and %)<br>• Control effectiveness scores (0.0 to 1.0) and gap statuses<br>• Scenario recalculation engine (`recalculate_scenario_risk`) | Serves as the mathematical ground truth. All monetary values and loss probabilities are strictly sourced from P2. |
| **P3: Graph & Attack Path Engine** | • Multi-hop attack graph topology<br>• Attack paths targeting critical business services<br>• Graph choke points where controls can disrupt traversal<br>• Business service dependency hierarchies and downtime cost ($/hr) | Identifies systemic threat propagation, choke points, and critical business impacts. |

---

## 2. Core Architectural Components

### 2.1 Natural Language Query Engine (`AIQueryEngine`)
The query engine routes incoming CISO inquiries to deterministic reasoning pipelines:
- **Semantic Intent Classifier**: Categorizes inquiries (Highest Financial Risk, Asset Explanation, EAL Ranking, Vulnerability Loss Attribution, Attack Paths, Weak Controls, Priority Remediation, ROI Investments, Simulations).
- **Zero-Hallucination Grounding**: Pulls verified telemetry and financial figures before constructing the response.
- **Structured Response Format**: Returns a standardized JSON object containing `answer`, `supporting_assets`, `supporting_risks`, `supporting_attack_paths`, `financial_metrics`, and `recommendations`.

### 2.2 Multi-Source Evidence Synthesizer (`EvidenceSynthesizer`)
Every claim made by the decision layer is backed by cross-layer internal evidence. For any given asset or risk driver, the synthesizer compiles:
1. **Internet Exposure**: Network exposure status and public IP assignment.
2. **Actively Exploited CVEs**: EPSS likelihood and CISA KEV listing.
3. **Privileged IAM Posture**: Standing privileged accounts lacking MFA.
4. **SIEM Telemetry**: Observed anomalous traffic, brute-force volume, or scanning.
5. **EDR Telemetry**: Real-time detection of credential harvesting (e.g. LSASS memory dumping).
6. **CSPM Posture**: Infrastructure configuration defects (e.g. open security groups).
7. **Business Service Dependency**: Mapped mission-critical business processes and downtime loss per hour.

### 2.3 Actionable Recommendation Engine (`RecommendationEngine`)
Calculates prioritized remediation actions across eight categories:
- **Patching**
- **MFA Enforcement**
- **Privileged Access Management (PAM)**
- **Network Segmentation**
- **Endpoint Detection & Response (EDR)**
- **Security Monitoring & SIEM**
- **Cloud Security Posture (CSPM)**
- **Access Restrictions**

Each recommendation provides:
- `action`: Specific remediation directive
- `reason`: Root cause analysis
- `affected_assets`: List of affected assets
- `current_risk`: Enterprise EAL prior to fix ($)
- `estimated_risk_after`: Enterprise EAL calculated by P2 after fix ($)
- `estimated_risk_reduction`: Calculated monetary risk reduction ($ and %)
- `cost_estimate`: Implementation and operational cost ($)
- `roi_ratio`: $\text{ROI} = \frac{\text{Estimated Risk Reduction}}{\text{Cost Estimate}}$
- `priority`: Priority classification (`CRITICAL`, `HIGH`, `MEDIUM`)
- `evidence`: Bulleted supporting telemetry

### 2.4 What-If Simulation Engine (`SimulationEngine`)
Allows executives to test hypothetical security actions and timeline modifications prior to capital expenditure:
- **MFA Across Privileged Accounts**: Identifies un-MFA'd privileged accounts in P1 IAM, evaluates broken links in P3 attack paths, and invokes P2 to calculate the resulting EAL drop.
- **Vulnerability Patching**: Simulates removal of specific CVEs and measures the severed attack path probability.
- **Network Segmentation**: Models isolation of critical databases from application subnets.
- **30-Day Remediation Delay**: Models the financial risk increase resulting from weaponization growth, active exploitation velocity, and SLA penalties.

---

## 3. Strict Guardrails & Anti-Hallucination Guarantees

To ensure complete trustworthiness for executive and board reporting, the decision layer implements hard guardrails:

> [!IMPORTANT]
> **Zero Fabrication Policy**:
> 1. **No Invented Financial Metrics**: EAL, VaR, SLE, and Risk Reduction values are never generated through language model extrapolation. They are strictly calculated and fetched from the P2 Quantitative Risk Engine.
> 2. **No Phantom CVEs or Assets**: All entities mentioned in queries are verified against the P1 registry.
> 3. **Deterministic "Insufficient data." Handling**: If a query references an entity not tracked in inventory, an uncalculated scenario, or out-of-scope data, the system returns `"Insufficient data."` along with the specific missing context.
> 4. **Mathematical Consistency**: The condition $\text{Current Risk} - \text{Risk Reduction} = \text{Estimated Risk After}$ is strictly validated across all recommendation and simulation endpoints.

---

## 4. Simulation Methodology & Mathematical Assumptions

### 4.1 Privileged MFA Rollout Methodology
1. **IAM Discovery**: Query P1 for accounts where `is_privileged == True` and `mfa_enabled == False`.
2. **Attack Path Evaluation**: Identify attack path steps in P3 utilizing credential dumping (T1003) or valid account abuse (T1078).
3. **P2 Recalculation**:
   - `CTRL-IAM-01` effectiveness increases from $0.20 \to 0.95$.
   - Lateral movement probability for compromised app tier credentials drops to near zero.
   - Enterprise EAL drops from **$3,420,000** to **$2,620,000** ($\Delta = -\$800,000$, $-23.4\%$).

### 4.2 30-Day Remediation Delay Methodology
Simulating a 30-day delay in remediation applies the following documented mathematical risk growth assumptions:
1. **Exploit Weaponization Growth**: As critical CVEs age without remediation, public exploit maturation increases threat actor attempt volume by $+40\%$.
2. **Threat Actor Campaign Convergence**: Active campaigns (e.g. FIN7 Operation ShadowVault) expand automated scanning against exposed targets.
3. **SLA Breach Penalty Multiplier**: Regulatory and compliance penalties compound for known critical CVEs remaining unpatched beyond defined SLAs.
4. **Calculated Outcome**:
   - Enterprise EAL increases from **$3,420,000** to **$4,140,000** ($+\$720,000$, $+21.05\%$).
   - 1-Year 95% VaR expands by $+28\%$.
   - Labeled with an explicit disclaimer: *"Simulated projection based on quantitative risk models; not historical data."*

---

## 5. API Reference

### 5.1 `POST /api/ai/query`
Executes an AI-assisted CISO query with full multi-source evidence.

**Request**:
```json
{
  "question": "Why is Payment API risky?"
}
```

**Response**:
```json
{
  "answer": "Payment API is currently a high financial risk because:\n\n1. It is internet exposed (Public IP: 198.51.100.42).\n2. It has actively exploited vulnerability in CISA KEV: CVE-2024-21413 (CVSS 9.8, EPSS 89.2%).\n3. A privileged account lacks MFA: 'admin_svc_pay' (Payment_Service_Admin).\n4. SIEM reports active suspicious telemetry: Brute Force / High-Volume Auth Anomaly (1420 events from 45.154.255.89).\n5. EDR telemetry detects high-severity activity: Credential Dumping (LSASS Memory Read) (T1003.001 via powershell.exe).\n6. CSPM identifies security misconfigurations: Open Security Group: Inbound rule allows 0.0.0.0/0 on sensitive port 8443 [PCI-DSS v4.0 Req 1.3 / CIS AWS 5.2].\n7. It directly supports the critical business service 'Payment Processing' (Tier 1 - Mission Critical), with downtime impact of $250,000/hr.\n\n**Quantitative Risk Summary**:\n- Expected Annual Loss (EAL): $2,054,000.00\n- Single Loss Expectancy: $3,950,000.00\n- Annual Loss Event Frequency: 0.52\n- 1-Year 95% VaR: $4,850,000.00",
  "supporting_assets": [
    {
      "asset_id": "asset-pay-01",
      "name": "Payment API",
      "type": "API Gateway & Microservice",
      "criticality": "Tier 1 - Mission Critical",
      "business_service": "Payment Processing",
      "internet_exposed": true
    }
  ],
  "supporting_risks": [
    {
      "driver_id": "rd-pay-cve",
      "name": "Active Exploitation of CVE-2024-21413 (RCE)",
      "category": "VULNERABILITY",
      "contribution_to_eal": 1180000.0,
      "percentage_contribution": 57.4
    }
  ],
  "supporting_attack_paths": [
    {
      "path_id": "AP-PAY-001",
      "name": "External RCE -> Credential Dump -> Lateral Movement to Payment DB",
      "target_business_service": "Payment Processing",
      "choke_points": [
        "Step 1: Ingress & CVE Patching (Payment API)",
        "Step 2: Privileged MFA Enforcement (admin_svc_pay)",
        "Step 3: Database Network Microsegmentation (Subnet 10.0.3.0/24)"
      ]
    }
  ],
  "financial_metrics": {
    "asset_expected_annual_loss": 2054000.0,
    "single_loss_expectancy": 3950000.0,
    "var_95": 4850000.0,
    "var_99": 7200000.0
  },
  "recommendations": [...]
}
```

---

### 5.2 `POST /api/ai/recommend`
Returns actionable, ROI-ranked security recommendations.

**Request**:
```json
{
  "limit": 3
}
```

**Response**:
```json
{
  "status": "success",
  "total_recommendations": 3,
  "recommendations": [
    {
      "action": "Deploy emergency vendor security patch for CVE-2024-21413 on Payment API",
      "reason": "Eliminates critical remote code execution flaw actively exploited by FIN7 in the wild.",
      "affected_assets": ["Payment API"],
      "current_risk": 3420000.0,
      "estimated_risk_after": 2240000.0,
      "estimated_risk_reduction": 1180000.0,
      "percentage_reduction": 34.5,
      "cost_estimate": 15000.0,
      "roi_ratio": 78.7,
      "priority": "CRITICAL",
      "category": "PATCHING",
      "evidence": [
        "Vulnerability CVE-2024-21413 has CVSS 9.8 and high exploit probability (EPSS 89.2%).",
        "Asset is directly internet exposed on public IP 198.51.100.42.",
        "Active CISA KEV listing and FIN7 Operation ShadowVault threat actor targeting.",
        "Directly severs Step 1 in Attack Path AP-PAY-001 protecting Payment Processing service."
      ]
    }
  ]
}
```

---

### 5.3 `POST /api/simulation/run`
Executes a what-if simulation scenario.

**Request**:
```json
{
  "scenario": "mfa_all_privileged"
}
```

**Response**:
```json
{
  "scenario": "MFA Enforcement Across All Privileged Accounts",
  "before_eal": 3420000.0,
  "after_eal": 2620000.0,
  "risk_reduction": 800000.0,
  "percentage_reduction": 23.39,
  "before_var_95": 7500000.0,
  "after_var_95": 5700000.0,
  "affected_assets": [
    "Payment API",
    "Payment Primary Database",
    "Internal Auth Service"
  ],
  "affected_attack_paths": [
    {
      "path_id": "AP-PAY-001",
      "name": "External RCE -> Credential Dump -> Lateral Movement to Payment DB",
      "disrupted_step": "Step 2: Dumps memory on host to extract un-MFA'd privileged service credentials.",
      "target_business_service": "Payment Processing"
    }
  ],
  "remediated_privileged_accounts": [
    "admin_svc_pay (Payment_Service_Admin)",
    "sec_operator_tier1 (Security_Operator)",
    "db_admin_root (Database_Administrator)"
  ],
  "assumptions": [
    "MFA enforced with FIDO2 / WebAuthn phishing-resistant hardware tokens across all privileged roles.",
    "Attacker credential reuse and automated password spray eliminated at ingress and lateral choke points.",
    "Control effectiveness for CTRL-IAM-01 increases from 0.20 to 0.95."
  ],
  "explanation": "Implementing MFA across all 3 privileged accounts eliminates credential-theft pivot vectors. Enterprise Expected Annual Loss (EAL) drops from $3,420,000.00 to $2,620,000.00, achieving a risk reduction of $800,000.00 (23.39% reduction)."
}
```

---

## 6. System Limitations & Operational Boundaries

1. **Dependence on Upstream Fidelity**: P4 explanations and risk reductions are as accurate as the telemetry ingested in P1 and the Monte Carlo distributions configured in P2.
2. **Simulation Boundaries**: What-if simulations represent quantitative mathematical risk projections based on documented risk parameters and threat intelligence velocity; they are not deterministic historical guarantees.
3. **Out-of-Band Assets**: Assets or cloud accounts not registered within P1 asset inventory are subject to the guardrail boundary and will trigger an `"Insufficient data."` response.
