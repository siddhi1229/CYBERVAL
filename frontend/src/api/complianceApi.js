import apiClient from './client';

export const complianceApi = {
  getComplianceCoverage: async () => {
    const response = await apiClient.get('/compliance');
    return response.data;
  },
  getControls: async () => {
    const response = await apiClient.get('/controls');
    return response.data;
  },
};

export default complianceApi;
