import apiClient from './client';

export const attackGraphApi = {
  getGraphTopology: async () => {
    const response = await apiClient.get('/attack-graph');
    return response.data;
  },
  calculateBlastRadius: async (nodeId) => {
    const response = await apiClient.post('/attack-graph/blast-radius', { nodeId });
    return response.data;
  },
  getShortestAttackPath: async (targetNodeId = 'db-core') => {
    const response = await apiClient.get(`/attack-graph/shortest-path?target=${targetNodeId}`);
    return response.data;
  }
};

export default attackGraphApi;
