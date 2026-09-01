import apiClient from './client';

export const attackGraphApi = {
  getGraphTopology: async () => {
    const response = await apiClient.get('/graph');
    const data = response.data;
    // Normalize into Cytoscape element collection format
    if (data && (data.nodes || data.edges)) {
      return {
        elements: {
          nodes: data.nodes || [],
          edges: data.edges || [],
        },
        summary: data.summary,
      };
    }
    return data;
  },
  calculateBlastRadius: async (nodeId) => {
    // Extract numeric ID if prefixed like 'asset-2'
    const numericId = typeof nodeId === 'string' && nodeId.includes('-') ? nodeId.split('-').pop() : nodeId;
    const response = await apiClient.get(`/assets/${numericId}/dependencies`);
    return response.data;
  },
  getShortestAttackPath: async (targetNodeId = '2') => {
    const numericId = typeof targetNodeId === 'string' && targetNodeId.includes('-') ? targetNodeId.split('-').pop() : targetNodeId;
    const response = await apiClient.get(`/attack-paths?target_asset_id=${numericId}`);
    return response.data;
  },
  getAttackPaths: async (limit = 20) => {
    const response = await apiClient.get(`/attack-paths?limit=${limit}`);
    return response.data;
  },
};

export default attackGraphApi;
