import axios from 'axios';
import {
  mockExecutiveData,
  mockTechnicalData,
  mockRiskModelingData,
  mockAttackGraphData,
  mockSimulationControls,
  mockInvestmentData,
  mockMasterComplianceData,
  mockAttackPaths,
  mockCopilotKnowledge,
  mockCopilotPrompts
} from './mockData';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';
const ENABLE_FALLBACK = import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cyberval_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor with graceful mock fallback (only if explicitly enabled via VITE_ENABLE_MOCK_FALLBACK=true)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (ENABLE_FALLBACK && (!error.response || error.response.status === 404 || error.response.status >= 500)) {
      console.warn(`[CYBERVAL Fallback Engine] Backend unreachable or 404 for ${originalRequest.url}. Serving offline demo fallback.`);
      const mockResponse = getMockResponseForUrl(originalRequest.url, originalRequest.method, originalRequest.data);
      if (mockResponse !== null) {
        return Promise.resolve({
          data: mockResponse,
          status: 200,
          statusText: 'OK (Mock Fallback)',
          headers: {},
          config: originalRequest,
        });
      }
    }
    return Promise.reject(error);
  }
);

function getMockResponseForUrl(url = '', method = 'get', requestData) {
  const cleanUrl = url.replace(/^\/api/, '').split('?')[0];

  if (cleanUrl.includes('/executive') || cleanUrl.includes('/risk/enterprise')) {
    return mockExecutiveData;
  }
  if (cleanUrl.includes('/technical/drilldown')) {
    return mockTechnicalData.drilldownTree;
  }
  if (cleanUrl.includes('/technical') || cleanUrl.includes('/assets')) {
    return mockTechnicalData;
  }
  if (cleanUrl.includes('/risk')) {
    return mockRiskModelingData;
  }
  if (cleanUrl.includes('/attack-paths')) {
    return mockAttackPaths;
  }
  if (cleanUrl.includes('/attack-graph') || cleanUrl.includes('/graph')) {
    return mockAttackGraphData;
  }
  if (cleanUrl.includes('/simulation/calculate') && method.toLowerCase() === 'post') {
    let parsedData = requestData;
    if (typeof requestData === 'string') {
      try { parsedData = JSON.parse(requestData); } catch (e) {}
    }
    return calculateSimulationResult(parsedData?.enabledControlIds || []);
  }
  if (cleanUrl.includes('/simulation/controls') || cleanUrl.includes('/simulation')) {
    return mockSimulationControls;
  }
  if (cleanUrl.includes('/investment')) {
    return mockInvestmentData;
  }
  if (cleanUrl.includes('/compliance')) {
    return mockMasterComplianceData;
  }
  if (cleanUrl.includes('/copilot/prompts')) {
    return mockCopilotPrompts;
  }
  if (cleanUrl.includes('/copilot/query') || cleanUrl.includes('/copilot/chat') || cleanUrl.includes('/ai/query')) {
    let query = '';
    if (typeof requestData === 'string') {
      try {
        const parsed = JSON.parse(requestData);
        query = parsed.query || parsed.message || '';
      } catch (e) {
        query = requestData;
      }
    } else if (requestData && (requestData.query || requestData.message)) {
      query = requestData.query || requestData.message;
    }
    return getCopilotResponse(query);
  }

  return null;
}

function calculateSimulationResult(enabledIds = []) {
  const baseRisk = 71;
  const baseEal = 18.4;
  let totalCost = 0;
  let totalReduction = 0;
  let scoreDelta = 0;

  mockSimulationControls.forEach(ctrl => {
    if (enabledIds.includes(ctrl.id)) {
      totalCost += ctrl.cost;
      totalReduction += ctrl.riskReduction;
      scoreDelta += ctrl.riskScoreImpact;
    }
  });

  const simulatedEal = Math.max(2.0, Number((baseEal - totalReduction).toFixed(1)));
  const simulatedScore = Math.max(15, Math.min(100, baseRisk + scoreDelta));
  const rosi = totalCost > 0 ? Number((((totalReduction - totalCost) / totalCost) * 100).toFixed(1)) : 0;

  return {
    before: {
      riskScore: baseRisk,
      eal: baseEal,
      financialExposure: 84.2,
      p95Loss: 31.7,
    },
    after: {
      riskScore: simulatedScore,
      eal: simulatedEal,
      financialExposure: Number((84.2 - totalReduction * 2.5).toFixed(1)),
      p95Loss: Number((31.7 - totalReduction * 1.6).toFixed(1)),
    },
    cost: Number(totalCost.toFixed(2)),
    reduction: Number(totalReduction.toFixed(2)),
    rosi: rosi,
    enabledControlsCount: enabledIds.length,
    paybackMonths: totalReduction > 0 ? Number(((totalCost / totalReduction) * 12).toFixed(1)) : 0
  };
}

function getCopilotResponse(query = '') {
  const normalized = query.toLowerCase();
  
  if (normalized.includes('highest') || normalized.includes('financial') || normalized.includes('highest risk')) {
    return mockCopilotKnowledge["highest financial cyber risk"];
  }
  if (normalized.includes('vulnerability') || normalized.includes('eal') || normalized.includes('contributes')) {
    return mockCopilotKnowledge["contributes most to eal"];
  }
  if (normalized.includes('fix first') || normalized.includes('priority') || normalized.includes('prioritize')) {
    return mockCopilotKnowledge["what should we fix first"];
  }
  if (normalized.includes('mfa') || normalized.includes('implement mfa') || normalized.includes('2fa')) {
    return mockCopilotKnowledge["what happens if we implement mfa"];
  }
  if (normalized.includes('rbi') || normalized.includes('sebi') || normalized.includes('compliance')) {
    return mockCopilotKnowledge["rbi and sebi"];
  }

  return {
    title: `Cyber-Risk Intelligence Analysis: "${query}"`,
    summary: `Based on current enterprise telemetry across our Core Banking, Payment Gateway, and Active Directory environments: Enterprise Risk Score is **71/100** with an Expected Annual Loss of **₹18.4 Cr**. 5 critical vulnerabilities and 7 attack paths are actively monitored.`,
    metrics: [
      { label: "Enterprise Risk Score", value: "71 / 100", badge: "High Risk" },
      { label: "Expected Annual Loss", value: "₹18.4 Cr", badge: "EAL" },
      { label: "P95 VaR Loss", value: "₹31.7 Cr", badge: "Tail Risk" },
      { label: "Max Potential Reduction", value: "₹6.5 Cr", badge: "Actionable" }
    ],
    recommendedAction: "Execute priority mitigations on MC-04 (Hardware MFA) and MC-11 (Micro-segmentation) to reduce financial exposure by up to ₹6.5 Cr with an aggregate ROSI of 400%.",
    deepLinks: [
      { label: "Executive Dashboard", path: "/executive" },
      { label: "Simulate Controls in What-If", path: "/simulation" },
      { label: "Inspect Attack Paths", path: "/attack-graph" }
    ]
  };
}

export default apiClient;
