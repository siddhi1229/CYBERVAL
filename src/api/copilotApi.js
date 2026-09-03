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
            { label: "Expected Annual Loss", value: "₹54.69 Cr", badge: "Baseline EAL" },
            { label: "Critical Assets at Risk", value: "Payment API (₹48 Cr)", badge: "Crown Jewel" },
            { label: "Top Threat Vector", value: "Fortinet Edge RCE + LSASS Dumping", badge: "Active T1003" },
            { label: "Optimized ROSI", value: "221.5%", badge: "P5 Knapsack" }
          ],
          recommendedAction: "Deploy INV-002 (Critical Patching Sprint) and INV-004 (Advanced EDR Memory Protection) to optimize financial risk reduction with maximum portfolio ROSI (221.5%).",
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
