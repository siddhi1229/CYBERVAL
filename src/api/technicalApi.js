import apiClient from './client';

export const technicalApi = {
  getOverview: async () => {
    const response = await apiClient.get('/technical');
    return response.data;
  },
  getDrilldownTree: async () => {
    const response = await apiClient.get('/technical/drilldown');
    return response.data;
  },
  getRemediationBacklog: async () => {
    const response = await apiClient.get('/technical/remediation-backlog');
    return response.data;
  },
  updateRemediationStatus: async (ticketId, status) => {
    const response = await apiClient.post(`/technical/remediation/${ticketId}/status`, { status });
    return response.data;
  },
};

export default technicalApi;
