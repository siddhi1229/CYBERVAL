import apiClient from './client';

export const riskApi = {
  getEnterpriseRisk: async () => {
    const response = await apiClient.get('/risk/enterprise');
    return response.data;
  },
  getAssetRisks: async () => {
    const response = await apiClient.get('/risk/assets');
    return response.data;
  },
  getThreats: async () => {
    const response = await apiClient.get('/threats');
    return response.data;
  },
};

export default riskApi;
