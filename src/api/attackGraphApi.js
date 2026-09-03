import apiClient from './client';

export const attackGraphApi = {
  getGraphTopology: async () => {
    const response = await apiClient.get('/graph');
    const data = response.data || {};
    
    // Normalize into Cytoscape element collection format
    const nodes = data.nodes || [];
    const edges = data.edges || [];

    return {
      elements: {
        nodes: nodes,
        edges: edges,
      },
      summary: data.summary || {
        totalNodes: nodes.length,
        totalEdges: edges.length,
      },
      killchainSummary: data.killchainSummary || {
        fastestAttackPath: 'Internet → Internet Gateway (CVE-2024-21762) → Payment API (CVE-2021-44228) → Payment Processing DB',
        estimatedTimeToCompromise: '~4.5 Hours',
        financialExposureAtRisk: '₹48 Cr',
      },
      crownJewelsAtRisk: ['PAYMENT-API-01', 'PAYMENT-DB-01', 'CUSTOMER-DB-01'],
    };
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
