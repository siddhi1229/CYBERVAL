import apiClient from './client';

export const copilotApi = {
  getSuggestedPrompts: async () => {
    const response = await apiClient.get('/copilot/prompts');
    return response.data;
  },
  askCopilot: async (query) => {
    const response = await apiClient.post('/copilot/query', { query });
    return response.data;
  }
};

export default copilotApi;
