// CYBERVAL High-Fidelity Cyber-Risk Intelligence Telemetry & Master Data Engine

export const mockExecutiveData = {
  enterpriseRiskScore: 71,
  enterpriseRiskScoreMax: 100,
  riskScoreDelta: -4.2, // Improvement
  expectedAnnualLoss: 18.4, // In Crores (₹)
  ealDelta: -1.8,
  totalFinancialExposure: 84.2, // In Crores
  p95Loss: 31.7, // In Crores
  p90Loss: 22.1,
  p99Loss: 48.9,
  potentialRiskReduction: 6.5, // In Crores
  currencySymbol: '₹',
  currencyUnit: 'Cr',
  lastUpdated: new Date().toISOString(),
  confidenceInterval: {
    low: 15.2,
    high: 21.8,
    confidenceLevel: '95%'
  },
  riskTrend: [
    { month: 'Sep 25', score: 79, eal: 23.5, p95: 39.2 },
    { month: 'Oct 25', score: 77, eal: 22.1, p95: 37.0 },
    { month: 'Nov 25', score: 76, eal: 21.4, p95: 35.8 },
    { month: 'Dec 25', score: 74, eal: 20.2, p95: 34.1 },
    { month: 'Jan 26', score: 73, eal: 19.5, p95: 33.0 },
    { month: 'Feb 26', score: 71, eal: 18.4, p95: 31.7 },
    { month: 'Mar 26 (Est)', score: 67, eal: 16.2, p95: 28.5 },
    { month: 'Apr 26 (Est)', score: 63, eal: 14.0, p95: 25.1 },
    { month: 'May 26 (Est)', score: 58, eal: 11.9, p95: 21.4 }
  ],
  topRiskContributors: [
    {
      id: 'RC-01',
      title: 'Ransomware Lateral Movement via Edge VPN',
      cve: 'CVE-2023-4966',
      threatActor: 'FIN7 / LockBit 3.0 Affiliate',
      businessImpact: 'Core Banking DB & Swift Settlement Gateway compromise',
      financialExposure: 32.5,
      ealContribution: 7.2, // ₹ Cr
      percentage: 39.1,
      status: 'Active Threat Path',
      severity: 'CRITICAL'
    },
    {
      id: 'RC-02',
      title: 'Kubernetes Cloud IAM Privilege Escalation',
      cve: 'CVE-2024-21887',
      threatActor: 'Nation-State / Advanced Persistent Threat',
      businessImpact: 'Unauthorized access to Digital Payment Gateway secrets',
      financialExposure: 21.0,
      ealContribution: 4.1,
      percentage: 22.3,
      status: 'Exploit Publicly Available',
      severity: 'HIGH'
    },
    {
      id: 'RC-03',
      title: 'Unauthenticated API SQLi in Customer Portal',
      cve: 'CVE-2023-38606',
      threatActor: 'Opportunistic Cybercrime Syndicate',
      businessImpact: 'PII Exfiltration & DPDP Act Regulatory Penalties',
      financialExposure: 16.4,
      ealContribution: 3.8,
      percentage: 20.6,
      status: 'Weaponized In Wild',
      severity: 'HIGH'
    },
    {
      id: 'RC-04',
      title: 'Legacy Remote Code Execution in Settlement App',
      cve: 'CVE-2021-44228',
      threatActor: 'Automated Botnets / Mirai Variant',
      businessImpact: 'Transaction processing disruption & SLA penalty',
      financialExposure: 9.8,
      ealContribution: 2.1,
      percentage: 11.4,
      status: 'Patch Overdue (38 Days)',
      severity: 'MEDIUM'
    },
    {
      id: 'RC-05',
      title: 'SaaS Integration OAuth Token Leakage',
      cve: 'CWE-522',
      threatActor: 'Supply Chain Compromise',
      businessImpact: 'Third-party vendor compromise of Wealth API',
      financialExposure: 4.5,
      ealContribution: 1.2,
      percentage: 6.6,
      status: 'Under Investigation',
      severity: 'MEDIUM'
    }
  ],
  criticalBusinessServices: [
    {
      id: 'BS-01',
      name: 'Core Banking & RTGS Settlement',
      unit: 'Retail & Corporate Banking',
      slaTier: 'Tier 1 (99.999%)',
      outageCostPerHour: '₹1.85 Cr/hr',
      riskScore: 84,
      financialExposure: 38.5,
      eal: 8.6,
      assetsCount: 42,
      criticalVulns: 5,
      status: 'ELEVATED RISK'
    },
    {
      id: 'BS-02',
      name: 'Digital Payment Gateway (UPI / IMPS)',
      unit: 'Digital Channels',
      slaTier: 'Tier 1 (99.99%)',
      outageCostPerHour: '₹1.20 Cr/hr',
      riskScore: 78,
      financialExposure: 24.0,
      eal: 5.2,
      assetsCount: 28,
      criticalVulns: 3,
      status: 'HIGH RISK'
    },
    {
      id: 'BS-03',
      name: 'Wealth Management & Trading API',
      unit: 'Capital Markets',
      slaTier: 'Tier 2 (99.9%)',
      outageCostPerHour: '₹65 Lakhs/hr',
      riskScore: 65,
      financialExposure: 12.5,
      eal: 2.8,
      assetsCount: 19,
      criticalVulns: 2,
      status: 'MODERATE RISK'
    },
    {
      id: 'BS-04',
      name: 'Corporate Treasury & FX Desk',
      unit: 'Treasury & Markets',
      slaTier: 'Tier 2 (99.9%)',
      outageCostPerHour: '₹40 Lakhs/hr',
      riskScore: 58,
      financialExposure: 6.2,
      eal: 1.1,
      assetsCount: 14,
      criticalVulns: 1,
      status: 'CONTROLLED'
    },
    {
      id: 'BS-05',
      name: 'Customer Identity Federation (SSO)',
      unit: 'Enterprise Security',
      slaTier: 'Tier 1 (99.99%)',
      outageCostPerHour: '₹30 Lakhs/hr',
      riskScore: 72,
      financialExposure: 3.0,
      eal: 0.7,
      assetsCount: 11,
      criticalVulns: 2,
      status: 'ATTENTION REQUIRED'
    }
  ],
  riskReductionOpportunities: [
    {
      id: 'RO-01',
      initiative: 'Hardware MFA (FIDO2) for Admin & Gateway Access',
      targetService: 'All Services (Perimeter & AD)',
      implementationCost: 0.45, // ₹ Cr
      ealReduction: 3.1, // ₹ Cr
      rosi: 588, // %
      timeToImplement: '3 Weeks',
      frameworkMapping: 'NIST PR.AC-7, RBI CSF 3.1, SEBI CSCRF 4.2.1'
    },
    {
      id: 'RO-02',
      initiative: 'Micro-segmentation & Zero Trust Network Access (ZTNA)',
      targetService: 'Core Banking & Settlement VNET',
      implementationCost: 0.60,
      ealReduction: 2.4,
      rosi: 300,
      timeToImplement: '6 Weeks',
      frameworkMapping: 'CIS 12.2, ISO A.13.1.3, RBI CSF 4.5'
    },
    {
      id: 'RO-03',
      initiative: 'Automated Vulnerability Patching Automation (<24h SLA)',
      targetService: 'Digital Payment Gateway',
      implementationCost: 0.25,
      ealReduction: 1.0,
      rosi: 300,
      timeToImplement: '2 Weeks',
      frameworkMapping: 'NIST PR.IP-12, ISO A.12.6.1, CIS 7.4'
    }
  ]
};

export const mockTechnicalData = {
  overview: {
    criticalVulnerabilities: 14,
    highVulnerabilities: 38,
    affectedAssets: 114,
    activeAttackPaths: 7,
    controlWeaknesses: 19,
    remediationBacklogTotal: 64,
    avgRemediationDays: 16.4,
    slaBreachesCount: 3,
    controlEffectivenessScore: 68.5 // %
  },
  // 6-Level Hierarchy Drilldown Tree
  drilldownTree: {
    id: 'ENT-01',
    level: 'Enterprise',
    name: 'CyberVal Global Financial Enterprise',
    riskScore: 71,
    eal: 18.4,
    units: [
      {
        id: 'BU-01',
        level: 'Business Unit',
        name: 'Retail & Corporate Banking',
        riskScore: 81,
        eal: 9.8,
        services: [
          {
            id: 'BS-01',
            level: 'Business Service',
            name: 'Core Banking & RTGS Settlement',
            riskScore: 84,
            eal: 8.6,
            assets: [
              {
                id: 'AST-001',
                level: 'Asset',
                name: 'srv-prod-db-core-01.bank.internal',
                ip: '10.240.12.88',
                type: 'Crown Jewel Database',
                criticality: 'CRITICAL',
                riskScore: 92,
                eal: 5.4,
                vulnerabilities: [
                  {
                    id: 'VULN-01',
                    level: 'Vulnerability',
                    cve: 'CVE-2023-4966',
                    name: 'Citrix NetScaler Unauthenticated Memory Leak (Session Hijack)',
                    cvss: 9.4,
                    epss: '96.2%',
                    exploitStatus: 'Weaponized & In-The-Wild',
                    controls: [
                      {
                        id: 'CTRL-01',
                        level: 'Control',
                        code: 'MC-04',
                        name: 'Multi-Factor Authentication & Ephemeral Session Tokens',
                        frameworks: 'NIST PR.AC-7 | ISO A.9.4.2 | RBI Annex 3.1 | SEBI 4.2.1',
                        status: 'PARTIALLY_IMPLEMENTED',
                        effectiveness: '45%',
                        actionRequired: 'Enforce hardware token rotation & patch build 13.1-49.13'
                      },
                      {
                        id: 'CTRL-02',
                        level: 'Control',
                        code: 'MC-11',
                        name: 'Network Micro-segmentation & Ingress Filtering',
                        frameworks: 'CIS 12.2 | NIST PR.AC-5 | RBI Annex 4.5',
                        status: 'NON_COMPLIANT',
                        effectiveness: '20%',
                        actionRequired: 'Isolate management console from standard employee subnet'
                      }
                    ]
                  },
                  {
                    id: 'VULN-02',
                    level: 'Vulnerability',
                    cve: 'CVE-2024-21887',
                    name: 'Ivanti Connect Secure Command Injection',
                    cvss: 9.1,
                    epss: '89.4%',
                    exploitStatus: 'Public Exploit Available',
                    controls: [
                      {
                        id: 'CTRL-03',
                        level: 'Control',
                        code: 'MC-08',
                        name: 'Automated Patch Management & Vulnerability Remediation',
                        frameworks: 'NIST PR.IP-12 | ISO A.12.6.1 | CIS 7.4 | SEBI 5.1',
                        status: 'IN_PROGRESS',
                        effectiveness: '60%',
                        actionRequired: 'Deploy vendor mitigation script and verify integrity hashes'
                      }
                    ]
                  }
                ]
              },
              {
                id: 'AST-002',
                level: 'Asset',
                name: 'k8s-ingress-gateway-01',
                ip: '10.240.10.15',
                type: 'Edge API Gateway',
                criticality: 'HIGH',
                riskScore: 78,
                eal: 2.1,
                vulnerabilities: [
                  {
                    id: 'VULN-03',
                    level: 'Vulnerability',
                    cve: 'CVE-2023-38606',
                    name: 'OAuth Token Forwarding SSRF',
                    cvss: 8.8,
                    epss: '74.1%',
                    exploitStatus: 'POC Available',
                    controls: [
                      {
                        id: 'CTRL-04',
                        level: 'Control',
                        code: 'MC-15',
                        name: 'Web Application Firewall & API Schema Validation',
                        frameworks: 'NIST PR.DS-5 | ISO A.14.2.5 | RBI Annex 6.2',
                        status: 'COMPLIANT',
                        effectiveness: '85%',
                        actionRequired: 'Update WAF regex rule set for SSRF mitigation'
                      }
                    ]
                  }
                ]
              }
            ]
          },
          {
            id: 'BS-04',
            level: 'Business Service',
            name: 'Corporate Treasury & FX Desk',
            riskScore: 58,
            eal: 1.2,
            assets: [
              {
                id: 'AST-003',
                level: 'Asset',
                name: 'treasury-fx-app-03',
                ip: '10.240.40.22',
                type: 'Application Server',
                criticality: 'HIGH',
                riskScore: 61,
                eal: 0.9,
                vulnerabilities: [
                  {
                    id: 'VULN-04',
                    level: 'Vulnerability',
                    cve: 'CVE-2021-44228',
                    name: 'Apache Log4j JNDI Remote Code Execution',
                    cvss: 10.0,
                    epss: '98.5%',
                    exploitStatus: 'Actively Exploited',
                    controls: [
                      {
                        id: 'CTRL-05',
                        level: 'Control',
                        code: 'MC-08',
                        name: 'Patch Management',
                        frameworks: 'NIST PR.IP-12 | ISO A.12.6.1',
                        status: 'NON_COMPLIANT',
                        effectiveness: '10%',
                        actionRequired: 'Upgrade log4j-core library to 2.17.1 immediately'
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        id: 'BU-02',
        level: 'Business Unit',
        name: 'Digital Channels & Mobile Banking',
        riskScore: 76,
        eal: 5.8,
        services: [
          {
            id: 'BS-02',
            level: 'Business Service',
            name: 'Digital Payment Gateway (UPI / IMPS)',
            riskScore: 78,
            eal: 5.2,
            assets: [
              {
                id: 'AST-004',
                level: 'Asset',
                name: 'upi-switch-master-01',
                ip: '10.240.20.5',
                type: 'Transaction Processing Switch',
                criticality: 'CRITICAL',
                riskScore: 86,
                eal: 3.8,
                vulnerabilities: [
                  {
                    id: 'VULN-05',
                    level: 'Vulnerability',
                    cve: 'CVE-2024-3400',
                    name: 'Palo Alto PAN-OS Command Injection',
                    cvss: 10.0,
                    epss: '97.2%',
                    exploitStatus: 'Weaponized',
                    controls: [
                      {
                        id: 'CTRL-06',
                        level: 'Control',
                        code: 'MC-19',
                        name: 'Next-Gen Firewall Threat Prevention Profile',
                        frameworks: 'NIST PR.AC-5 | ISO A.13.1.1 | RBI Annex 4.1',
                        status: 'COMPLIANT',
                        effectiveness: '90%',
                        actionRequired: 'Apply Threat ID 95187 signature package'
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        id: 'BU-03',
        level: 'Business Unit',
        name: 'Capital Markets & Wealth Management',
        riskScore: 65,
        eal: 2.8,
        services: [
          {
            id: 'BS-03',
            level: 'Business Service',
            name: 'Wealth Management & Trading API',
            riskScore: 65,
            eal: 2.8,
            assets: [
              {
                id: 'AST-005',
                level: 'Asset',
                name: 'wealth-broker-api-01',
                ip: '10.240.30.12',
                type: 'Trading API Gateway',
                criticality: 'MEDIUM',
                riskScore: 65,
                eal: 1.8,
                vulnerabilities: [
                  {
                    id: 'VULN-06',
                    level: 'Vulnerability',
                    cve: 'CVE-2023-48795',
                    name: 'SSH Terrapin Prefix Truncation Attack',
                    cvss: 5.9,
                    epss: '32.1%',
                    exploitStatus: 'Academic POC',
                    controls: [
                      {
                        id: 'CTRL-07',
                        level: 'Control',
                        code: 'MC-22',
                        name: 'Cryptographic Protocol Hardening',
                        frameworks: 'NIST PR.DS-2 | ISO A.10.1.1 | SEBI 4.6',
                        status: 'PARTIALLY_IMPLEMENTED',
                        effectiveness: '70%',
                        actionRequired: 'Disable ChaCha20-Poly1305 and CBC ciphers'
                      }
                    ]
                  }
                ]
              }
            ]
          }
        ]
      }
    ]
  },
  remediationBacklog: [
    {
      id: 'REM-101',
      cve: 'CVE-2023-4966',
      title: 'Citrix NetScaler Gateway Session Hijack',
      asset: 'srv-prod-db-core-01 & NetScaler VIP',
      businessService: 'Core Banking & RTGS',
      cvss: 9.4,
      epss: 0.96,
      slaDaysRemaining: -4, // Breached
      slaStatus: 'BREACHED',
      assignedTeam: 'SecOps - Perimeter',
      financialExposure: '₹32.5 Cr',
      priority: 'P0 - CRITICAL'
    },
    {
      id: 'REM-102',
      cve: 'CVE-2024-3400',
      title: 'PAN-OS Command Injection Vulnerability',
      asset: 'upi-switch-master-01',
      businessService: 'Digital Payment Gateway',
      cvss: 10.0,
      epss: 0.97,
      slaDaysRemaining: 1,
      slaStatus: 'EXPIRING_SOON',
      assignedTeam: 'Network Engineering',
      financialExposure: '₹24.0 Cr',
      priority: 'P0 - CRITICAL'
    },
    {
      id: 'REM-103',
      cve: 'CVE-2024-21887',
      title: 'Ivanti VPN Command Execution Flaw',
      asset: 'vpn-gw-external-02',
      businessService: 'Enterprise Identity & Remote Access',
      cvss: 9.1,
      epss: 0.89,
      slaDaysRemaining: 3,
      slaStatus: 'ON_TRACK',
      assignedTeam: 'Cloud Infrastructure',
      financialExposure: '₹14.2 Cr',
      priority: 'P1 - HIGH'
    },
    {
      id: 'REM-104',
      cve: 'CVE-2021-44228',
      title: 'Apache Log4j JNDI RCE in Legacy Treasury',
      asset: 'treasury-fx-app-03',
      businessService: 'Corporate Treasury & FX Desk',
      cvss: 10.0,
      epss: 0.98,
      slaDaysRemaining: -12,
      slaStatus: 'BREACHED',
      assignedTeam: 'AppDev - Treasury',
      financialExposure: '₹6.2 Cr',
      priority: 'P0 - CRITICAL'
    },
    {
      id: 'REM-105',
      cve: 'CVE-2023-38606',
      title: 'OAuth SSRF in Ingress Gateway',
      asset: 'k8s-ingress-gateway-01',
      businessService: 'Core Banking Ingress',
      cvss: 8.8,
      epss: 0.74,
      slaDaysRemaining: 7,
      slaStatus: 'ON_TRACK',
      assignedTeam: 'SecOps - AppSec',
      financialExposure: '₹8.4 Cr',
      priority: 'P1 - HIGH'
    }
  ]
};

export const mockRiskModelingData = {
  simulationIterations: 50000,
  confidenceLevel: 95,
  expectedAnnualLoss: 18.4,
  p50Loss: 14.8,
  p90Loss: 22.1,
  p95Loss: 31.7,
  p99Loss: 48.9,
  maxSimulatedLoss: 84.2,
  lossExceedanceCurve: [
    { loss: 5, probability: 99.2, exceedancePercent: '99.2%', confidenceRange: [4.8, 5.2] },
    { loss: 10, probability: 88.5, exceedancePercent: '88.5%', confidenceRange: [9.4, 10.6] },
    { loss: 15, probability: 64.1, exceedancePercent: '64.1%', confidenceRange: [14.1, 15.9] },
    { loss: 18.4, probability: 50.0, exceedancePercent: '50.0% (EAL)', confidenceRange: [17.3, 19.5] },
    { loss: 22.1, probability: 30.0, exceedancePercent: '30.0% (P90)', confidenceRange: [20.8, 23.4] },
    { loss: 31.7, probability: 5.0, exceedancePercent: '5.0% (P95 VaR)', confidenceRange: [29.9, 33.5] },
    { loss: 48.9, probability: 1.0, exceedancePercent: '1.0% (P99 Tail)', confidenceRange: [46.2, 51.6] },
    { loss: 65, probability: 0.3, exceedancePercent: '0.3%', confidenceRange: [61.0, 69.0] },
    { loss: 84.2, probability: 0.05, exceedancePercent: '0.05% (Max Exposure)', confidenceRange: [79.0, 89.4] }
  ],
  fairDecomposition: {
    threatEventFrequency: {
      annualEvents: '14.2 / yr',
      contactFrequency: 'High (Internet-Facing)',
      threatCapability: 'Tier 4 (Financially Motivated Ransomware Groups)'
    },
    vulnerabilityResistance: {
      overallStrength: '54% (Moderate)',
      perimeterDefense: '62%',
      lateralMovementDefense: '38%',
      dataProtection: '58%'
    },
    lossMagnitude: {
      primaryLosses: {
        productivityLoss: 4.8, // ₹ Cr
        responseCost: 2.1,
        replacementCost: 1.5
      },
      secondaryLosses: {
        rbiSebiRegulatoryFines: 4.2, // DPDP / RBI / SEBI
        ransomExtortionDemand: 3.5,
        reputationalBrandDamage: 2.3
      }
    }
  },
  scenarioStressTests: [
    {
      scenario: 'Catastrophic Ransomware Encryption on Core Banking',
      lossProbability: '3.4% / yr',
      p95Exposure: '₹42.8 Cr',
      primaryDriver: 'Lateral movement via unpatched VPN + Domain Admin compromise',
      keyControlMitigant: 'Zero Trust Micro-segmentation & Immutable Backups'
    },
    {
      scenario: 'High-Volume Payment Gateway Transaction Fraud / Spoofing',
      lossProbability: '6.8% / yr',
      p95Exposure: '₹28.4 Cr',
      primaryDriver: 'API token forgery and unauthenticated endpoint access',
      keyControlMitigant: 'FIDO2 Hardware MFA & Mutual TLS API Federation'
    },
    {
      scenario: 'Extensive Customer PII Data Exfiltration (DPDP Violation)',
      lossProbability: '8.1% / yr',
      p95Exposure: '₹19.6 Cr',
      primaryDriver: 'SQL injection on customer trading portal',
      keyControlMitigant: 'Database Activity Monitoring & Column-Level Encryption'
    }
  ]
};

export const mockAttackGraphData = {
  elements: [
    // Nodes
    { data: { id: 'internet', label: 'Internet / Threat Actors', type: 'internet', tier: 'Perimeter', criticality: 'INFO', exposure: 0, status: 'Hostile' } },
    { data: { id: 'vpn-gw', label: 'Citrix NetScaler VPN GW', type: 'vpn', ip: '194.88.21.4', tier: 'Perimeter', criticality: 'CRITICAL', cve: 'CVE-2023-4966', cvss: 9.4, epss: '96.2%', status: 'Vulnerable', financialRisk: 32.5 } },
    { data: { id: 'dmz-proxy', label: 'DMZ Reverse Proxy (Nginx)', type: 'server', ip: '10.240.10.4', tier: 'DMZ', criticality: 'MEDIUM', status: 'Hardened', financialRisk: 8.2 } },
    { data: { id: 'k8s-ingress', label: 'K8s Ingress API Gateway', type: 'server', ip: '10.240.10.15', tier: 'DMZ', criticality: 'HIGH', cve: 'CVE-2023-38606', cvss: 8.8, epss: '74.1%', status: 'Vulnerable', financialRisk: 14.5 } },
    { data: { id: 'user-admin', label: 'Domain Admin (Compromised)', type: 'user', role: 'Enterprise Admin', tier: 'Internal', criticality: 'CRITICAL', status: 'Compromised Session', financialRisk: 28.0 } },
    { data: { id: 'user-developer', label: 'DevOps Lead Identity', type: 'user', role: 'K8s Cluster Admin', tier: 'Internal', criticality: 'HIGH', status: 'Active', financialRisk: 12.0 } },
    { data: { id: 'ad-server', label: 'Active Directory DC-01', type: 'server', ip: '10.240.12.10', tier: 'Internal', criticality: 'CRITICAL', status: 'High Privilege', financialRisk: 42.0 } },
    { data: { id: 'jump-host', label: 'Treasury Bastion Jump Host', type: 'server', ip: '10.240.12.50', tier: 'Internal', criticality: 'HIGH', cve: 'CVE-2021-44228', cvss: 10.0, epss: '98.5%', status: 'Vulnerable', financialRisk: 18.0 } },
    { data: { id: 'db-core', label: 'Core Banking DB (Oracle RAC)', type: 'database', ip: '10.240.12.88', tier: 'Crown Jewel', criticality: 'CRITICAL', isCrownJewel: true, status: 'Crown Jewel Target', financialRisk: 38.5 } },
    { data: { id: 'db-payment', label: 'Payment Switch DB (PostgreSQL)', type: 'database', ip: '10.240.20.10', tier: 'Crown Jewel', criticality: 'CRITICAL', isCrownJewel: true, status: 'Crown Jewel Target', financialRisk: 24.0 } },
    { data: { id: 'srv-core-banking', label: 'Core Banking Service', type: 'service', tier: 'Business Service', criticality: 'CRITICAL', status: 'Active', financialRisk: 38.5 } },
    { data: { id: 'srv-upi-payment', label: 'UPI / IMPS Payment Service', type: 'service', tier: 'Business Service', criticality: 'CRITICAL', status: 'Active', financialRisk: 24.0 } },
    
    // Edges (Attack vectors & relationships)
    { data: { id: 'e1', source: 'internet', target: 'vpn-gw', label: 'Exploit CVE-2023-4966 (Session Leak)', isAttackPath: true, exploitability: 0.96, protocol: 'HTTPS/443' } },
    { data: { id: 'e2', source: 'internet', target: 'k8s-ingress', label: 'OAuth Token Injection', isAttackPath: false, exploitability: 0.74, protocol: 'HTTPS/443' } },
    { data: { id: 'e3', source: 'vpn-gw', target: 'user-admin', label: 'Hijack Active Admin Session', isAttackPath: true, exploitability: 0.94, protocol: 'Memory Dump' } },
    { data: { id: 'e4', source: 'k8s-ingress', target: 'user-developer', label: 'ServiceAccount Token Extraction', isAttackPath: false, exploitability: 0.70, protocol: 'KubeAPI' } },
    { data: { id: 'e5', source: 'user-admin', target: 'ad-server', label: 'Kerberoasting & DCSync', isAttackPath: true, exploitability: 0.88, protocol: 'LDAP/Kerberos' } },
    { data: { id: 'e6', source: 'ad-server', target: 'jump-host', label: 'RDP with Admin Privileges', isAttackPath: true, exploitability: 0.85, protocol: 'RDP/3389' } },
    { data: { id: 'e7', source: 'jump-host', target: 'db-core', label: 'DBA Credential Dump -> Direct SQL Injection', isAttackPath: true, exploitability: 0.95, protocol: 'Oracle/1521' } },
    { data: { id: 'e8', source: 'user-developer', target: 'db-payment', label: 'Direct Cloud SQL IAM Bypass', isAttackPath: false, exploitability: 0.65, protocol: 'PG/5432' } },
    { data: { id: 'e9', source: 'db-core', target: 'srv-core-banking', label: 'Data Corruption / Ransomware Extortion', isAttackPath: true, exploitability: 1.0, protocol: 'Service Disruption' } },
    { data: { id: 'e10', source: 'db-payment', target: 'srv-upi-payment', label: 'Transaction Interception / Forgery', isAttackPath: false, exploitability: 0.8, protocol: 'Service Disruption' } }
  ],
  killchainSummary: {
    fastestAttackPath: 'Internet → Citrix VPN (CVE-2023-4966) → Domain Admin → Active Directory → Jump Host → Core Banking Oracle RAC',
    stepsCount: 5,
    estimatedTimeToCompromise: '3.5 Hours',
    financialExposureAtRisk: '₹38.5 Cr',
    primaryWeakness: 'Missing FIDO2 MFA on perimeter & unrestricted lateral RPC/SMB between jump hosts and databases'
  }
};

export const mockSimulationControls = [
  {
    id: 'ctrl_mfa',
    name: 'Hardware MFA Enforcement (FIDO2 / YubiKey)',
    category: 'Identity & Access',
    cost: 0.45, // ₹ Cr
    riskReduction: 3.1, // ₹ Cr
    riskScoreImpact: -11,
    enabled: true,
    description: 'Enforce hardware security keys across all admin consoles, VPNs, and privileged jump hosts, completely eliminating session hijacking.'
  },
  {
    id: 'ctrl_patching',
    name: 'Automated 24h Critical Vulnerability Patching SLA',
    category: 'Vulnerability Management',
    cost: 0.25,
    riskReduction: 1.2,
    riskScoreImpact: -5,
    enabled: true,
    description: 'Automate zero-day patch deployments on all perimeter and Tier 1 banking infrastructure within 24 hours of public disclosure.'
  },
  {
    id: 'ctrl_segmentation',
    name: 'Micro-segmentation & Zero Trust Network Access (ZTNA)',
    category: 'Network Security',
    cost: 0.60,
    riskReduction: 2.4,
    riskScoreImpact: -9,
    enabled: true,
    description: 'Enforce software-defined micro-segmentation between DMZ, application tiers, and crown jewel database subnets.'
  },
  {
    id: 'ctrl_edr',
    name: 'Next-Gen EDR / XDR with Automated Ransomware Isolation',
    category: 'Endpoint Security',
    cost: 0.35,
    riskReduction: 1.5,
    riskScoreImpact: -6,
    enabled: false,
    description: 'Deploy advanced behavioral endpoint detection on all domain controllers and core banking server clusters.'
  },
  {
    id: 'ctrl_pam',
    name: 'Privileged Access Management (PAM) with Ephemeral Secrets',
    category: 'Identity & Access',
    cost: 0.40,
    riskReduction: 1.8,
    riskScoreImpact: -7,
    enabled: false,
    description: 'Enforce just-in-time privileged access with full session recording, zero standing domain admin privileges.'
  },
  {
    id: 'ctrl_cspm',
    name: 'Cloud Security Posture Management & IAM Guardrails',
    category: 'Cloud Security',
    cost: 0.20,
    riskReduction: 0.9,
    riskScoreImpact: -4,
    enabled: false,
    description: 'Continuous drift detection and automated remediation of Kubernetes and cloud IAM misconfigurations.'
  },
  {
    id: 'ctrl_dam',
    name: 'Database Activity Monitoring (DAM) & Field Encryption',
    category: 'Data Protection',
    cost: 0.30,
    riskReduction: 1.1,
    riskScoreImpact: -4,
    enabled: false,
    description: 'Hardware-accelerated encryption at rest and real-time SQL exfiltration monitoring on crown jewel tables.'
  }
];

export const mockInvestmentData = {
  totalBudget: 3.5, // ₹ Cr
  allocatedBudget: 1.3, // ₹ Cr
  unallocatedBudget: 2.2, // ₹ Cr
  currentRiskScore: 71,
  targetRiskScore: 42,
  currentEal: 18.4, // ₹ Cr
  projectedEal: 11.9, // ₹ Cr
  totalRiskReductionAchievable: 6.5, // ₹ Cr
  portfolioRosi: 400.0, // %
  efficientFrontier: [
    { investment: 0.0, riskReduction: 0.0, eal: 18.4, rosi: 0 },
    { investment: 0.45, riskReduction: 3.1, eal: 15.3, rosi: 588 },
    { investment: 0.70, riskReduction: 4.3, eal: 14.1, rosi: 514 },
    { investment: 1.30, riskReduction: 6.7, eal: 11.7, rosi: 415 }, // Optimal Point
    { investment: 1.70, riskReduction: 7.8, eal: 10.6, rosi: 358 },
    { investment: 2.10, riskReduction: 8.5, eal: 9.9, rosi: 304 },
    { investment: 2.60, riskReduction: 9.1, eal: 9.3, rosi: 250 },
    { investment: 3.20, riskReduction: 9.4, eal: 9.0, rosi: 193 } // Diminishing Returns
  ],
  recommendedInitiatives: [
    {
      id: 'INV-01',
      title: 'FIDO2 Hardware MFA Rollout across All Privileged Surfaces',
      domain: 'Identity & Access',
      cost: 0.45,
      riskReduction: 3.1,
      rosi: 588.9,
      paybackPeriod: '1.8 Months',
      priorityRank: 1,
      status: 'APPROVED_FOR_BUDGET'
    },
    {
      id: 'INV-02',
      title: 'Zero Trust Micro-segmentation for Core Banking VNET',
      domain: 'Network Defense',
      cost: 0.60,
      riskReduction: 2.4,
      rosi: 300.0,
      paybackPeriod: '3.0 Months',
      priorityRank: 2,
      status: 'APPROVED_FOR_BUDGET'
    },
    {
      id: 'INV-03',
      title: 'Privileged Access Management (PAM) Vault Integration',
      domain: 'Access Control',
      cost: 0.40,
      riskReduction: 1.8,
      rosi: 350.0,
      paybackPeriod: '2.7 Months',
      priorityRank: 3,
      status: 'UNDER_REVIEW'
    },
    {
      id: 'INV-04',
      title: 'Automated 24h Patching Engine for Edge & K8s',
      domain: 'Vulnerability Management',
      cost: 0.25,
      riskReduction: 1.2,
      rosi: 380.0,
      paybackPeriod: '2.5 Months',
      priorityRank: 4,
      status: 'APPROVED_FOR_BUDGET'
    },
    {
      id: 'INV-05',
      title: 'Database Activity Monitoring & Real-time Exfiltration Blocker',
      domain: 'Data Protection',
      cost: 0.30,
      riskReduction: 1.1,
      rosi: 266.7,
      paybackPeriod: '3.3 Months',
      priorityRank: 5,
      status: 'PROPOSED'
    }
  ]
};

// Master Control Mapping Database (Unified Engine across NIST, ISO, CIS, RBI, SEBI)
export const mockMasterComplianceData = {
  overallComplianceScore: 78.4, // %
  frameworkScores: {
    iso27001: 82.1,
    nistCsf: 79.5,
    cisControls: 74.8,
    rbiCyberFramework: 76.0,
    sebiCscrf: 79.6
  },
  frameworkStats: [
    { name: 'ISO/IEC 27001:2022', score: 82, totalControls: 93, compliant: 76, partial: 12, nonCompliant: 5 },
    { name: 'NIST CSF 2.0', score: 80, totalControls: 106, compliant: 84, partial: 15, nonCompliant: 7 },
    { name: 'CIS Controls v8', score: 75, totalControls: 153, compliant: 114, partial: 27, nonCompliant: 12 },
    { name: 'RBI Cyber Security Framework', score: 76, totalControls: 68, compliant: 52, partial: 11, nonCompliant: 5 },
    { name: 'SEBI CSCRF Framework', score: 80, totalControls: 84, compliant: 67, partial: 12, nonCompliant: 5 }
  ],
  masterControls: [
    {
      id: 'MC-01',
      code: 'MC-01',
      title: 'Enterprise Cyber Asset & Topology Inventory',
      domain: 'Asset Management',
      status: 'COMPLIANT',
      evidenceStatus: 'Automated Daily Discovery Active',
      lastAudited: '2026-02-15',
      evidenceUrl: 'telemetry://assets/inventory-sync-log',
      financialRiskContribution: '₹1.8 Cr',
      affectedAssetsCount: 114,
      frameworks: {
        nist: 'ID.AM-01 / ID.AM-02',
        iso: 'A.8.1 (Inventory of assets)',
        cis: 'CIS 1.1 / CIS 1.2 (Inventory & Control of Enterprise Assets)',
        rbi: 'RBI Annexure-I Section 1 (Inventory Management)',
        sebi: 'SEBI CSCRF Chapter II (Governance & Asset Register)'
      }
    },
    {
      id: 'MC-02',
      code: 'MC-02',
      title: 'Cryptographic Protection & Key Management',
      domain: 'Data Protection',
      status: 'COMPLIANT',
      evidenceStatus: 'HSM Cluster Level-3 FIPS Validated',
      lastAudited: '2026-02-10',
      evidenceUrl: 'telemetry://crypto/hsm-audit-cert',
      financialRiskContribution: '₹2.4 Cr',
      affectedAssetsCount: 48,
      frameworks: {
        nist: 'PR.DS-01 / PR.DS-02',
        iso: 'A.8.24 (Use of cryptography)',
        cis: 'CIS 3.10 / CIS 3.11 (Encrypt Sensitive Data)',
        rbi: 'RBI Annexure-I Section 7 (Key & Encryption Standards)',
        sebi: 'SEBI CSCRF Chapter IV Section 4.6 (Data Protection & Encryption)'
      }
    },
    {
      id: 'MC-04',
      code: 'MC-04',
      title: 'Multi-Factor Authentication & Identity Federation',
      domain: 'Identity & Access Control',
      status: 'PARTIAL',
      evidenceStatus: 'Hardware MFA active for 65% of admins; legacy SMS on 35%',
      lastAudited: '2026-02-22',
      evidenceUrl: 'telemetry://iam/mfa-enforcement-report',
      financialRiskContribution: '₹7.2 Cr',
      affectedAssetsCount: 92,
      frameworks: {
        nist: 'PR.AA-01 / PR.AA-05 (MFA & Identity Assurance)',
        iso: 'A.5.17 / A.8.5 (Authentication information & Secure authentication)',
        cis: 'CIS 6.3 / CIS 6.4 (Require MFA for Externally-Exposed & Admin Apps)',
        rbi: 'RBI Annexure-I Section 3.1 (Mandatory 2FA/MFA for Admin access)',
        sebi: 'SEBI CSCRF Chapter IV Section 4.2 (Identity & Access Control Standards)'
      }
    },
    {
      id: 'MC-08',
      code: 'MC-08',
      title: 'Automated Vulnerability Management & SLA Patching',
      domain: 'Vulnerability Management',
      status: 'PARTIAL',
      evidenceStatus: '3 SLA breaches on P0 CVEs in Treasury & Edge gateways',
      lastAudited: '2026-02-24',
      evidenceUrl: 'telemetry://vuln/patch-sla-tracker',
      financialRiskContribution: '₹6.5 Cr',
      affectedAssetsCount: 42,
      frameworks: {
        nist: 'ID.RA-01 / PR.IP-12 (Vulnerability Management)',
        iso: 'A.8.8 (Management of technical vulnerabilities)',
        cis: 'CIS 7.4 / CIS 7.5 (Automated Patch Management)',
        rbi: 'RBI Annexure-I Section 5 (Vulnerability Assessment & Timely Patching)',
        sebi: 'SEBI CSCRF Chapter V Section 5.1 (Vulnerability Remediation Timelines)'
      }
    },
    {
      id: 'MC-11',
      code: 'MC-11',
      title: 'Network Micro-segmentation & Zero Trust Boundary',
      domain: 'Network Defense',
      status: 'NON_COMPLIANT',
      evidenceStatus: 'Flat network routing between Jump Host and Core Banking DB',
      lastAudited: '2026-02-18',
      evidenceUrl: 'telemetry://network/flow-matrix-gap',
      financialRiskContribution: '₹8.6 Cr',
      affectedAssetsCount: 54,
      frameworks: {
        nist: 'PR.IR-01 / PR.IR-02 (Network Security & Micro-segmentation)',
        iso: 'A.8.20 / A.8.22 (Network controls & Segregation)',
        cis: 'CIS 12.2 / CIS 12.3 (Establish and Maintain a Secure Network Architecture)',
        rbi: 'RBI Annexure-I Section 4.5 (Network Segmentation & DMZ Isolation)',
        sebi: 'SEBI CSCRF Chapter IV Section 4.4 (Network Security Architecture)'
      }
    },
    {
      id: 'MC-14',
      code: 'MC-14',
      title: 'Continuous Security Telemetry & 24x7 SOC Monitoring',
      domain: 'Detection & Monitoring',
      status: 'COMPLIANT',
      evidenceStatus: 'SIEM/SOAR ingestion at 45k EPS with 99.98% uptime',
      lastAudited: '2026-02-20',
      evidenceUrl: 'telemetry://soc/siem-heartbeat',
      financialRiskContribution: '₹1.5 Cr',
      affectedAssetsCount: 114,
      frameworks: {
        nist: 'DE.AE-02 / DE.CM-01 (Security Continuous Monitoring)',
        iso: 'A.8.16 (Monitoring activities)',
        cis: 'CIS 8.2 / CIS 8.5 (Centralized Audit Log & SIEM Alerting)',
        rbi: 'RBI Annexure-I Section 8 (Continuous SOC & Log Retention 1-Year)',
        sebi: 'SEBI CSCRF Chapter VI Section 6.1 (24x7 Security Operations Center)'
      }
    },
    {
      id: 'MC-18',
      code: 'MC-18',
      title: 'Cyber Incident Response, Forensics & Regulatory Reporting',
      domain: 'Incident Response & Resilience',
      status: 'COMPLIANT',
      evidenceStatus: 'CERT-In & RBI 6-hour automated reporting workflow active',
      lastAudited: '2026-02-12',
      evidenceUrl: 'telemetry://ir/playbook-drill-q4',
      financialRiskContribution: '₹3.2 Cr',
      affectedAssetsCount: 114,
      frameworks: {
        nist: 'RS.RP-01 / RS.CO-02 (Incident Response & Reporting)',
        iso: 'A.5.24 / A.5.26 (Incident management & Response learning)',
        cis: 'CIS 17.1 / CIS 17.3 (Designate and Maintain Incident Response Plan)',
        rbi: 'RBI Annexure-I Section 11 (Mandatory Incident Reporting within 6 Hours)',
        sebi: 'SEBI CSCRF Chapter VII Section 7.2 (Cyber Incident Notification & Forensics)'
      }
    }
  ]
};

export const mockCopilotPrompts = [
  "What is our highest financial cyber risk?",
  "Which vulnerability contributes most to EAL?",
  "What should we fix first?",
  "What happens if we implement MFA?",
  "How compliant are we with RBI and SEBI cybersecurity frameworks?",
  "Show the top 3 attack paths leading to Core Banking Oracle DB"
];

export const mockCopilotKnowledge = {
  "highest financial cyber risk": {
    title: "Highest Financial Cyber Risk Analysis",
    summary: "Our single highest financial cyber risk is **Ransomware Lateral Movement via Edge VPN Gateway (CVE-2023-4966)**, targeting the **Core Banking Oracle DB & Swift Settlement Gateway**.",
    metrics: [
      { label: "Financial Exposure at Risk", value: "₹32.5 Cr", badge: "Critical" },
      { label: "Expected Annual Loss (EAL)", value: "₹7.2 Cr", badge: "39.1% of Total EAL" },
      { label: "Estimated Time to Exploit", value: "3.5 Hours", badge: "High Velocity" },
      { label: "Root Control Weakness", value: "MC-04 (MFA) & MC-11 (Micro-segmentation)", badge: "Actionable" }
    ],
    recommendedAction: "Execute Emergency Remediation: Deploy NetScaler firmware upgrade and enforce FIDO2 Hardware MFA on external access. Expected risk reduction: ₹3.1 Cr EAL with 588% ROSI.",
    deepLinks: [
      { label: "Inspect Attack Path in Attack Graph", path: "/attack-graph" },
      { label: "Simulate MFA in What-If Engine", path: "/simulation" },
      { label: "View Technical Remediation Ticket (REM-101)", path: "/technical" }
    ]
  },
  "contributes most to eal": {
    title: "Vulnerability EAL Contribution Breakdown",
    summary: "**CVE-2023-4966** (Citrix Bleed Memory Leak) contributes **₹7.2 Cr** (39.1%) to our total EAL, followed by **CVE-2024-21887** (Ivanti Command Injection) at **₹4.1 Cr** (22.3%) and **CVE-2023-38606** (K8s OAuth SSRF) at **₹3.8 Cr** (20.6%).",
    metrics: [
      { label: "Top Vulnerability", value: "CVE-2023-4966", badge: "CVSS 9.4" },
      { label: "Total Top 3 EAL Impact", value: "₹15.1 Cr", badge: "82% of Exposure" },
      { label: "Weaponization Status", value: "Active in Wild", badge: "Immediate Patch Required" }
    ],
    recommendedAction: "Prioritize patching CVE-2023-4966 and CVE-2024-21887 within the next 24 hours to eliminate ₹11.3 Cr of financial exposure.",
    deepLinks: [
      { label: "View Vulnerabilities in Technical Dashboard", path: "/technical" },
      { label: "Open Investment Optimization", path: "/investment" }
    ]
  },
  "what should we fix first": {
    title: "Prioritized Remediation Recommendation (ROSI-Ranked)",
    summary: "Based on ROSI (Return on Security Investment) and financial risk reduction, here is the prioritized action sequence:",
    metrics: [
      { label: "1. Hardware MFA (FIDO2)", value: "Cost: ₹45L | Reduction: ₹3.1 Cr | ROSI: 588%", badge: "Rank #1" },
      { label: "2. Patch CVE-2023-4966 & CVE-2024-3400", value: "Cost: ₹25L | Reduction: ₹1.0 Cr | ROSI: 300%", badge: "Rank #2" },
      { label: "3. Core Banking Micro-segmentation", value: "Cost: ₹60L | Reduction: ₹2.4 Cr | ROSI: 300%", badge: "Rank #3" }
    ],
    recommendedAction: "Funding these top 3 controls will consume **₹1.30 Cr** of capital while eliminating **₹6.5 Cr of EAL** (bringing enterprise risk score down from 71 to 52).",
    deepLinks: [
      { label: "Load in What-If Simulator", path: "/simulation" },
      { label: "Review Security Investment Portfolio", path: "/investment" }
    ]
  },
  "what happens if we implement mfa": {
    title: "What-If Simulation: MFA Enforcement (FIDO2)",
    summary: "Enforcing Hardware MFA (FIDO2) across all external access and administrator workstations generates the single highest risk reduction across all simulated controls.",
    metrics: [
      { label: "Current EAL", value: "₹18.4 Cr", badge: "Before" },
      { label: "Projected EAL with MFA", value: "₹15.3 Cr", badge: "After (-₹3.1 Cr)" },
      { label: "Implementation Cost", value: "₹45 Lakhs", badge: "Capital" },
      { label: "Return on Security Investment", value: "588.9%", badge: "Exceptional ROI" },
      { label: "Risk Score Impact", value: "71 → 60 (-11 pts)", badge: "Score Delta" }
    ],
    recommendedAction: "Proceed with enterprise FIDO2 rollout. This directly addresses Master Control MC-04, satisfying RBI Cyber Security Framework Annexure-I 3.1 and SEBI CSCRF 4.2.1 mandates.",
    deepLinks: [
      { label: "Adjust Control in What-If Engine", path: "/simulation" },
      { label: "Inspect Master Control MC-04", path: "/compliance" }
    ]
  },
  "rbi and sebi": {
    title: "Regulatory Compliance Posture: RBI CSF & SEBI CSCRF",
    summary: "Our compliance posture across Indian Financial Cyber Regulations is **76.0% for RBI Cyber Security Framework** and **79.6% for SEBI CSCRF**.",
    metrics: [
      { label: "RBI CSF Status", value: "76% Compliant", badge: "5 Non-Compliant Controls" },
      { label: "SEBI CSCRF Status", value: "79.6% Compliant", badge: "5 Non-Compliant Controls" },
      { label: "Critical Regulatory Gap", value: "MC-11 (Micro-segmentation) & MC-08 (Patch SLAs)", badge: "Audit Flag" },
      { label: "Regulatory Penalty Exposure", value: "₹4.2 Cr (Potential fines & scrutiny)", badge: "Secondary Loss" }
    ],
    recommendedAction: "Resolve MC-08 patch SLA breaches and configure network isolation for Core Banking to achieve 90%+ audit compliance readiness before next regulatory review cycle.",
    deepLinks: [
      { label: "Open Master Compliance Engine", path: "/compliance" },
      { label: "Check Risk Impact in FAIR Analysis", path: "/risk" }
    ]
  }
};
