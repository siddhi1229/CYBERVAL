import apiClient from './client';

export const copilotApi = {
  getSuggestedPrompts: async () => {
    // Executive prompt templates grounded in enterprise risk
    return [
      "What is our highest financial cyber risk?",
      "Which asset contributes most to expected annual loss?",
      "What attack paths target our crown jewel databases?",
      "What is the projected risk reduction if we enforce MFA?",
      "What are our regulatory compliance gaps across RBI and SEBI?",
    ];
  },
  askCopilot: async (query) => {
    const response = await apiClient.post('/ai/query', { question: query });
    return response.data;
  },
  getRecommendation: async (query) => {
    const response = await apiClient.post('/ai/recommend', { question: query });
    return response.data;
  },
};

export default copilotApi;
