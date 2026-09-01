import apiClient from './client';

export const executiveApi = {
  getOverview: async () => {
    const response = await apiClient.get('/executive');
    return response.data;
  },
  getRiskTrend: async (timeframe = '12m') => {
    const response = await apiClient.get(`/executive/trend?timeframe=${timeframe}`);
    return response.data;
  },
  getTopContributors: async () => {
    const response = await apiClient.get('/executive/top-contributors');
    return response.data;
  },
  getCriticalServices: async () => {
    const response = await apiClient.get('/executive/critical-services');
    return response.data;
  },
  getReductionOpportunities: async () => {
    const response = await apiClient.get('/executive/reduction-opportunities');
    return response.data;
  },
};

export default executiveApi;
