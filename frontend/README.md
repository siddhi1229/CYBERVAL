# CYBERVAL Frontend | Enterprise Cyber-Risk Intelligence Platform

Reserved for the shared React/Vite application. Consumes the platform API at `http://localhost:8000`.

Welcome to **CYBERVAL**, an enterprise cyber-risk intelligence, financial exposure forecasting, and regulatory compliance platform.

Built by **P6 (Frontend Engineer)** as part of the CYBERVAL team.

---

## Tech Stack

- **Framework**: React 18 (with React Router v6)
- **Bundler / Build Tool**: Vite
- **Styling**: Tailwind CSS (Obsidian Dark Cyber-Risk Palette)
- **HTTP Client**: Axios (with base URL proxy to `http://localhost:8000`)
- **Charting & Visualizations**: Recharts (Loss Exceedance Curves, Efficient Frontier, Trajectories)
- **Graph & Killchain Engine**: Cytoscape.js (`cytoscape-dagre`, `cytoscape-cola`)
- **Icons**: Lucide React

---

## Routes & Capabilities

| Route | Dashboard / Module | Key Telemetry & Capabilities |
|---|---|---|
| `/executive` | **Executive Dashboard** | Enterprise Risk Score, Expected Annual Loss (EAL), P95 VaR, Actionable Risk Reduction, Critical Services & Top Contributors |
| `/technical` | **Technical Intelligence** | Critical Vulnerabilities (CVEs, CVSS, EPSS), 6-Level Hierarchy Drilldown (`Enterprise -> BU -> Service -> Asset -> Vuln -> Control`), SLA Backlogs |
| `/risk` | **Quantitative Risk (FAIR)** | Monte Carlo Loss Exceedance Curve, Loss Frequency vs Loss Magnitude, Primary vs Secondary Loss breakdown, Stress Testing |
| `/attack-graph` | **Interactive Attack Graph** | Cytoscape.js interactive topology (`Internet -> VPN -> Servers -> Users -> DBs -> Services`), Killchain Highlighting, Dynamic Blast Radius Calculator |
| `/simulation` | **What-If Engine** | Interactive Control Knobs (MFA, Patching, EDR, Micro-segmentation, PAM, CSPM, DAM), Real-time Before/After/Reduction/Cost/ROSI computation |
| `/investment` | **Security Investment** | Capital Budget Optimization, ROSI ranking, Investment vs Risk Reduction Efficient Frontier curve |
| `/compliance` | **Master Compliance Engine** | Unified Master Control Mapping across **ISO/IEC 27001**, **NIST CSF 2.0**, **CIS Controls v8**, **RBI Cyber Security Framework**, **SEBI CSCRF** |
| `/copilot` | **AI Cyber-Risk Copilot** | Natural Language Executive Queries (*"What is our highest risk?"*, *"What should we fix first?"*, *"What happens if we implement MFA?"*) |
| `/reports` | **Executive Reports** | Consolidated Executive Board Briefing & Regulatory Audit Evidence Document |

---

## Backend API Integration

CYBERVAL Frontend communicates with the backend REST APIs at `http://localhost:8000/api` via Axios.

- **Base URL**: Configurable via `.env` (`VITE_API_BASE_URL=http://localhost:8000/api`)
- **Core Platform Endpoints**:
  - `GET /api/risk/enterprise`: Total Expected Annual Loss and enterprise risk summary
  - `GET /api/risk/assets`: Asset-level financial risk quantification
  - `GET /api/graph`: Cytoscape-compatible enterprise digital twin graph
  - `GET /api/attack-paths`: Prioritized attack traversal paths
  - `GET /api/assets/{id}/dependencies`: Downstream blast radius and connected assets
  - `GET /api/correlation/asset/{id}`: 360-degree multi-source telemetry convergence
  - `POST /api/investment/optimize`: 0/1 Knapsack capital budget optimization
  - `GET /api/investment/curves`: Diminishing returns curve data points
  - `GET /api/compliance`: Regulatory control mappings across NIST, ISO, CIS, RBI, SEBI
  - `POST /api/ai/query`: Risk-grounded AI decision support and recommendations

---

## Development & Build Scripts

```bash
# From within the frontend directory:
cd frontend

# Install dependencies
npm install

# Start local development server (Vite on http://localhost:5173)
npm run dev

# Build production bundle
npm run build

# Preview production build
npm run preview
```
