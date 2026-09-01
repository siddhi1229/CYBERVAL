import apiClient from './client';

export const complianceApi = {
  getMasterMapping: async () => {
    const response = await apiClient.get('/compliance');
    return response.data;
  },
  getControlsByFramework: async (frameworkKey) => {
    const response = await apiClient.get(`/compliance/framework/${frameworkKey}`);
    return response.data;
  },
  updateControlStatus: async (controlId, status, evidenceNote) => {
    const response = await apiClient.post(`/compliance/controls/${controlId}/status`, { status, evidenceNote });
    return response.data;
  }
};

export default complianceApi;
