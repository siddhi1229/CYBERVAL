import apiClient from './client';

export const executiveApi = {
  getOverview: async () => {
    // Parallel fetch across real backend endpoints
    const [enterpriseRes, assetRisksRes, assetsRes, vulnsRes] = await Promise.all([
      apiClient.get('/risk/enterprise'),
      apiClient.get('/risk/assets'),
      apiClient.get('/assets'),
      apiClient.get('/vulnerabilities'),
    ]);

    const enterprise = enterpriseRes.data;
    const assetRisks = assetRisksRes.data || [];
    const assets = assetsRes.data || [];
    const vulnerabilities = vulnsRes.data || [];

    // Map assets by ID for fast lookup
    const assetMap = new Map();
    assets.forEach((a) => assetMap.set(a.id, a));

    // Map vulnerabilities by asset_id
    const vulnByAsset = new Map();
    vulnerabilities.forEach((v) => {
      if (!vulnByAsset.has(v.asset_id)) vulnByAsset.set(v.asset_id, []);
      vulnByAsset.get(v.asset_id).push(v);
    });

    // Compute top risk contributors from real asset risks
    const topRiskContributors = assetRisks.slice(0, 10).map((r, idx) => {
      const asset = assetMap.get(r.asset_id);
      const vulns = vulnByAsset.get(r.asset_id) || [];
      const primaryVuln = vulns[0];
      return {
        id: `RC-${idx + 1}`,
        assetId: r.asset_id,
        assetName: asset?.name || `Asset #${r.asset_id}`,
        title: primaryVuln ? `${primaryVuln.cve_id} on ${asset?.name || 'Asset'}` : `Risk on ${asset?.name || 'Asset'}`,
        cve: primaryVuln?.cve_id || 'N/A',
        severity: primaryVuln?.severity || 'HIGH',
        financialExposure: r.financial_impact,
        ealContribution: r.expected_annual_loss,
        likelihood: r.likelihood,
        owner: asset?.owner || 'Unknown',
        internetExposed: asset?.internet_exposed ?? false,
        criticality: asset?.criticality || 'MEDIUM',
      };
    });

    // Group assets by business services if available
    const serviceMap = new Map();
    assets.forEach((a) => {
      const sName = a.department || a.owner || 'General Infrastructure';
      if (!serviceMap.has(sName)) {
        serviceMap.set(sName, { name: sName, assetCount: 0, criticalCount: 0 });
      }
      const s = serviceMap.get(sName);
      s.assetCount += 1;
      if (a.criticality?.toLowerCase() === 'critical') s.criticalCount += 1;
    });

    const criticalBusinessServices = Array.from(serviceMap.values()).map((s, idx) => ({
      id: `BS-${idx + 1}`,
      name: s.name,
      assetCount: s.assetCount,
      criticalAssets: s.criticalCount,
    }));

    return {
      totalExpectedAnnualLoss: enterprise.total_expected_annual_loss,
      riskCount: enterprise.risk_count,
      highestRiskAssetId: enterprise.highest_risk_asset_id,
      calculationVersion: enterprise.calculation_version,
      topRiskContributors,
      criticalBusinessServices,
      totalAssetsCount: assets.length,
      criticalVulnerabilitiesCount: vulnerabilities.filter((v) => v.severity?.toLowerCase() === 'critical').length,
    };
  },
};

export default executiveApi;
