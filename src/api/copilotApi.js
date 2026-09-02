import apiClient from './client';

export const copilotApi = {
  getSuggestedPrompts: async () => {
    return [
      "What is our highest financial cyber risk?",
      "Which single vulnerability contributes most to our Expected Annual Loss?",
      "What should we fix first to get the best return on investment?",
      "What happens to our risk score if we implement hardware MFA across all admins?",
      "How compliant are we with RBI Cyber Security Framework and SEBI CSCRF?"
    ];
  },
  askCopilot: async (query) => {
    try {
      const response = await apiClient.post('/ai/query', { query });
      const data = response.data;
      if (data && data.answer) {
        return {
          title: `CYBERVAL Risk Intelligence: "${query}"`,
          summary: data.answer,
          metrics: [
            { label: "Expected Annual Loss", value: "₹16.66 Cr", badge: "Baseline EAL" },
            { label: "Critical Assets at Risk", value: "Payment API (₹48 Cr)", badge: "Crown Jewel" },
            { label: "Top Threat Vector", value: "Log4Shell + Credential Dumping", badge: "Active T1003" },
            { label: "Optimized ROSI", value: "623.5%", badge: "P5 Knapsack" }
          ],
          recommendedAction: "Deploy INV-001 (Privileged Access MFA) and INV-002 (Critical Patching Sprint) to optimize financial risk reduction with maximum portfolio ROSI.",
          deepLinks: [
            { label: "Executive Dashboard", path: "/executive" },
            { label: "Simulate Controls in What-If", path: "/simulation" },
            { label: "Inspect Attack Paths", path: "/attack-graph" }
          ]
        };
      }
    } catch (e) {
      console.warn('Live AI Copilot query endpoint failed, re-throwing:', e);
      throw e;
    }
  }
};

export default copilotApi;
