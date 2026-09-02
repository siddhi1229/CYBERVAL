import apiClient from './client';

export const investmentApi = {
  getOverview: async () => {
    try {
      const [curvesRes, optRes, controlsRes] = await Promise.all([
        apiClient.get('/investment/curves'),
        apiClient.post('/investment/optimize', { total_budget: 13000000.0 }),
        apiClient.get('/investment/controls'),
      ]);
      const curves = curvesRes.data;
      const opt = optRes.data;
      const controls = controlsRes.data;

      const baselineEalCr = Number(((curves.baseline_enterprise_eal || 100000000) / 10000000).toFixed(2));
      const totalBudgetCr = Number(((opt.total_budget || 13000000) / 10000000).toFixed(2));
      const committedCr = Number(((opt.total_investment || 8500000) / 10000000).toFixed(2));
      const reductionCr = Number(((opt.total_risk_reduction || 61500000) / 10000000).toFixed(2));
      const residualEalCr = Number(((opt.residual_enterprise_eal || 38500000) / 10000000).toFixed(2));

      const frontier = (curves.data_points || []).map((pt) => ({
        investment: Number((pt.cumulative_investment / 10000000).toFixed(2)),
        riskReduction: Number((pt.cumulative_risk_reduction / 10000000).toFixed(2)),
        eal: Number((pt.residual_eal / 10000000).toFixed(2)),
        rosi: pt.marginal_rosi_pct || 0,
        controlAdded: pt.control_name || '',
      }));

      const topCandidates = (controls || []).map((c) => ({
        id: c.id,
        name: c.name,
        targetAsset: c.target_asset_or_risk || 'ENTERPRISE',
        cost: Number((c.annual_cost / 10000000).toFixed(2)),
        riskReduction: Number(((c.risk_reduction || 0) / 10000000).toFixed(2)),
        effectiveness: Math.round((c.effectiveness || 0.5) * 100),
        rosi: c.rosi ? Math.round(c.rosi.rosi_percentage) : 0,
        status: opt.selected_controls.some((sc) => sc.id === c.id) ? 'RECOMMENDED' : 'EVALUATING',
        description: c.description || '',
      }));

      return {
        totalBudget: totalBudgetCr || 2.0,
        allocatedBudget: committedCr,
        portfolioRosi: Math.round(opt.portfolio_aggregate_rosi || 623),
        totalRiskReduction: reductionCr,
        baselineEal: baselineEalCr,
        residualEal: residualEalCr,
        currentRiskScore: 71,
        projectedRiskScore: Math.max(15, Math.round(71 - (reductionCr / (baselineEalCr || 10)) * 40)),
        efficientFrontier: frontier.length > 0 ? frontier : [
          { investment: 0, riskReduction: 0, eal: baselineEalCr, rosi: 0 },
          { investment: committedCr, riskReduction: reductionCr, eal: residualEalCr, rosi: Math.round(opt.portfolio_aggregate_rosi || 623) }
        ],
        topCandidateControls: topCandidates,
      };
    } catch (e) {
      console.warn('Live investment API failed, re-throwing:', e);
      throw e;
    }
  },
  getEfficientFrontier: async () => {
    const response = await apiClient.get('/investment/curves');
    return response.data;
  },
  optimizeBudget: async (totalBudget) => {
    const budgetValue = typeof totalBudget === 'number' && totalBudget < 1000 ? totalBudget * 10000000 : totalBudget;
    const response = await apiClient.post('/investment/optimize', { total_budget: budgetValue });
    return response.data;
  },
  getControls: async () => {
    const response = await apiClient.get('/investment/controls');
    return response.data;
  },
};

export default investmentApi;
