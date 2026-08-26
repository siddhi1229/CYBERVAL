// Days 1-2 Enterprise Cyber Risk Digital Twin Master Schema & Data
const enterpriseGraphData = {
  // 1. ALL REQUIRED ENTITY TYPES (NODES)
  nodes: [
    // Users & Identities
    { id: "U1", label: "Alice Smith", type: "User", role: "DevOps Engineer" },
    { id: "ID1", label: "admin_service_account", type: "Identity", privilege: "Domain Admin" },

    // Assets & Dependencies
    { id: "A1", label: "Employee Workstation", type: "Asset", riskScore: 3 },
    { id: "A2", label: "Production Web Server", type: "Asset", riskScore: 7 },
    { id: "DEP1", label: "Node.js Runtime v14", type: "Dependency", status: "Outdated" },

    // Vulnerabilities
    { id: "V1", label: "CVE-2023-38606 (RCE)", type: "Vulnerability", cvssScore: 9.8 },

    // Controls
    { id: "C1", label: "Web Application Firewall (WAF)", type: "Control", effectiveness: 0.85 },
    { id: "C2", label: "Multi-Factor Authentication (MFA)", type: "Control", effectiveness: 0.95 },

    // Business Services
    { id: "BS1", label: "Payment Gateway", type: "BusinessService", criticality: "High" },

    // Threats
    { id: "T1", label: "APT29 (Cozy Bear)", type: "Threat", threatLevel: "Critical" }
  ],

  // 2. ALL REQUIRED RELATIONSHIPS (EDGES)
  edges: [
    { source: "U1", target: "ID1", relation: "ASSUMES_IDENTITY" },
    { source: "ID1", target: "A1", relation: "ACCESSES" },
    { source: "A1", target: "A2", relation: "CONNECTS_TO" },
    { source: "A2", target: "DEP1", relation: "HAS_DEPENDENCY" },
    { source: "A2", target: "V1", relation: "EXPOSED_TO" },
    { source: "C1", target: "A2", relation: "PROTECTS" },
    { source: "C2", target: "ID1", relation: "ENFORCED_ON" },
    { source: "A2", target: "BS1", relation: "POWERS_SERVICE" },
    { source: "T1", target: "V1", relation: "EXPLOITS" }
  ]
};

module.exports = enterpriseGraphData;