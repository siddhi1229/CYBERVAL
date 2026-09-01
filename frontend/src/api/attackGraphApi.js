import apiClient from './client';

export const attackGraphApi = {
  getGraphTopology: async () => {
    const response = await apiClient.get('/graph');
    return response.data;
  },
  getAttackPaths: async (params = {}) => {
    const response = await apiClient.get('/attack-paths', { params });
    return response.data;
  },
  getAssetDependencies: async (assetId) => {
    const response = await apiClient.get(`/assets/${assetId}/dependencies`);
    return response.data;
  },
  getAssetAttackPaths: async (assetId) => {
    const response = await apiClient.get(`/assets/${assetId}/attack-paths`);
    return response.data;
  },
  getAssetCorrelation: async (assetId) => {
    const response = await apiClient.get(`/correlation/asset/${assetId}`);
    return response.data;
  },
};

export default attackGraphApi;
