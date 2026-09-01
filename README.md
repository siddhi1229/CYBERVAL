# CYBERVAL Frontend | Enterprise Cyber-Risk Intelligence Platform

Welcome to **CYBERVAL**, an enterprise cyber-risk intelligence, financial exposure forecasting, and regulatory compliance platform.

Built by **P6 (Frontend Engineer)** as part of the CYBERVAL team.

---

## 🛠️ Tech Stack

- **Framework**: React 18 (with React Router v6)
- **Bundler / Build Tool**: Vite
- **Styling**: Tailwind CSS (Obsidian Dark Cyber-Risk Palette)
- **HTTP Client**: Axios (with base URL proxy and live fallback telemetry engine)
- **Charting & Visualizations**: Recharts (Loss Exceedance Curves, Efficient Frontier, Trajectories)
- **Graph & Killchain Engine**: Cytoscape.js (`cytoscape-dagre`, `cytoscape-cola`)
- **Icons**: Lucide React

---

## 🚀 Routes & Capabilities

| Route | Dashboard / Module | Key Telemetry & Capabilities |
|---|---|---|
| `/executive` | **Executive Dashboard** | Enterprise Risk Score (71/100), Expected Annual Loss (₹18.4 Cr), P95 VaR (₹31.7 Cr), Potential Risk Reduction (₹6.5 Cr), Trajectory, Critical Services & Top Contributors |
| `/technical` | **Technical Intelligence** | Critical Vulnerabilities (CVEs, CVSS, EPSS), 6-Level Hierarchy Drilldown (`Enterprise -> BU -> Service -> Asset -> Vuln -> Control`), SLA Backlogs |
| `/risk` | **Quantitative Risk (FAIR)** | Monte Carlo Loss Exceedance Curve (50k trials), Loss Frequency vs Loss Magnitude, Primary vs Secondary Loss breakdown, Stress Testing |
| `/attack-graph` | **Interactive Attack Graph** | Cytoscape.js interactive topology (`Internet -> VPN -> Servers -> Users -> DBs -> Services`), Killchain Highlighting, Dynamic Blast Radius Calculator |
| `/simulation` | **What-If Engine** | Interactive Control Knobs (MFA, Patching, EDR, Micro-segmentation, PAM, CSPM, DAM), Real-time Before/After/Reduction/Cost/ROSI computation |
| `/investment` | **Security Investment** | Capital Budget Optimization, ROSI ranking, Investment vs Risk Reduction Efficient Frontier curve |
| `/compliance` | **Master Compliance Engine** | Unified Master Control Mapping across **ISO/IEC 27001**, **NIST CSF 2.0**, **CIS Controls v8**, **RBI Cyber Security Framework**, **SEBI CSCRF** |
| `/copilot` | **AI Cyber-Risk Copilot** | Natural Language Executive Queries (*"What is our highest risk?"*, *"What should we fix first?"*, *"What happens if we implement MFA?"*) |

---

## 🔌 Backend API Integration (Coordinated with P1)

CYBERVAL Frontend communicates with the backend REST APIs using the centralized Axios client in `src/api/client.js`.

- **Base URL**: Configurable via `.env` (`VITE_API_BASE_URL=http://localhost:8000/api`)
- **API Endpoints**:
  - `GET /api/executive`: Executive KPIs, trend, and risk contributors
  - `GET /api/technical`: Critical vulnerabilities and 6-level drilldown tree
  - `GET /api/risk`: FAIR parameters and Monte Carlo loss exceedance distributions
  - `GET /api/attack-graph`: Node and edge topology elements for Cytoscape.js
  - `POST /api/simulation/calculate`: What-If control toggles and ROSI calculation
  - `GET /api/investment`: Security budget and efficient frontier curve
  - `GET /api/compliance`: Harmonized Master Controls mapped to ISO, NIST, CIS, RBI, SEBI
  - `POST /api/copilot/query`: Executive NLP queries

---

## 💻 Development & Build Scripts

```bash
# Start local development server (Vite on http://localhost:5173)
npm run dev

# Build production bundle
npm run build

# Preview production build
npm run preview
```
