import apiClient from './client';

export const technicalApi = {
  getAssets: async (params = {}) => {
    const response = await apiClient.get('/assets', { params });
    return response.data;
  },
  getVulnerabilities: async (params = {}) => {
    const response = await apiClient.get('/vulnerabilities', { params });
    return response.data;
  },
  getCveCatalog: async (params = {}) => {
    const response = await apiClient.get('/vulnerabilities/catalog', { params });
    return response.data;
  },
  getSecurityEvents: async (params = {}) => {
    const response = await apiClient.get('/security-events', { params });
    return response.data;
  },
  getEdrEvents: async (params = {}) => {
    const response = await apiClient.get('/edr/events', { params });
    return response.data;
  },
  getCspmFindings: async (params = {}) => {
    const response = await apiClient.get('/cspm/findings', { params });
    return response.data;
  },
  getIamUsers: async (params = {}) => {
    const response = await apiClient.get('/iam/users', { params });
    return response.data;
  },
  getIamAccess: async (params = {}) => {
    const response = await apiClient.get('/iam/access', { params });
    return response.data;
  },
  getAssetCorrelation: async (assetId) => {
    const response = await apiClient.get(`/correlation/asset/${assetId}`);
    return response.data;
  },
};

export default technicalApi;
