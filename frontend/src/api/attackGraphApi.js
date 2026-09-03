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
        estimatedTimeToCompromise: '~1.5 Hours',
        financialExposureAtRisk: '₹48 Cr',
      },
      crownJewelsAtRisk: ['PAYMENT-API-01', 'PAYMENT-DB-01', 'CUSTOMER-DB-01'],
    };
  },
  calculateBlastRadius: async (nodeId) => {
    const numericId = typeof nodeId === 'string' && nodeId.includes('-') ? nodeId.split('-').pop() : nodeId;
    const response = await apiClient.get(`/assets/${numericId}/dependencies`);
    return response.data;
  },
  getShortestAttackPath: async (targetNodeId = '2') => {
    const numericId = typeof targetNodeId === 'string' && targetNodeId.includes('-') ? targetNodeId.split('-').pop() : targetNodeId;
    const response = await apiClient.get(`/attack-paths?target_asset_id=${numericId}`);
    return response.data;
  },
  getAttackPaths: async (limitOrParams = 50) => {
    let url = '/attack-paths';
    let config = {};
    if (typeof limitOrParams === 'number' || typeof limitOrParams === 'string') {
      config = { params: { limit: limitOrParams } };
    } else if (typeof limitOrParams === 'object' && limitOrParams !== null) {
      config = { params: limitOrParams };
    }
    const response = await apiClient.get(url, config);
    return response.data;
  },
  getAssetDependencies: async (assetId) => {
    const numericId = typeof assetId === 'string' && assetId.includes('-') ? assetId.split('-').pop() : assetId;
    const response = await apiClient.get(`/assets/${numericId}/dependencies`);
    return response.data;
  },
};

export default attackGraphApi;
