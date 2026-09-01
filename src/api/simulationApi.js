import apiClient from './client';

export const simulationApi = {
  getControls: async () => {
    const response = await apiClient.get('/simulation/controls');
    return response.data;
  },
  calculateScenario: async (enabledControlIds = []) => {
    const response = await apiClient.post('/simulation/calculate', { enabledControlIds });
    return response.data;
  }
};

export default simulationApi;
