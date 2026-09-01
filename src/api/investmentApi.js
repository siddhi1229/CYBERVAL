import apiClient from './client';

export const investmentApi = {
  getOverview: async () => {
    const response = await apiClient.get('/investment');
    return response.data;
  },
  getEfficientFrontier: async () => {
    const response = await apiClient.get('/investment/frontier');
    return response.data;
  },
  optimizeBudget: async (totalBudget) => {
    const response = await apiClient.post('/investment/optimize', { totalBudget });
    return response.data;
  }
};

export default investmentApi;
