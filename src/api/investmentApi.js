import apiClient from './client';

export const investmentApi = {
  getOverview: async (budgetInCr = 0.5) => {
    try {
      const budgetBytes = typeof budgetInCr === 'number' && budgetInCr < 1000 
        ? budgetInCr * 10000000.0 
        : Number(budgetInCr || 5000000.0);

      const [curvesRes, optRes, controlsRes] = await Promise.all([
        apiClient.get('/investment/curves'),
        apiClient.post('/investment/optimize', { total_budget: budgetBytes }),
        apiClient.get('/investment/controls'),
      ]);
      const curves = curvesRes.data || {};
      const opt = optRes.data || {};
      const controls = controlsRes.data || [];

      const baselineEalCr = Number(((curves.baseline_enterprise_eal || opt.baseline_enterprise_eal || 546893130) / 10000000).toFixed(2));
      const totalBudgetCr = Number(((opt.total_budget || budgetBytes) / 10000000).toFixed(2));
      const committedCr = Number(((opt.total_investment || 0) / 10000000).toFixed(2));
      const reductionCr = Number(((opt.total_risk_reduction || 0) / 10000000).toFixed(2));
      const residualEalCr = Number(((opt.residual_enterprise_eal || Math.max(0, baselineEalCr * 10000000 - (opt.total_risk_reduction || 0))) / 10000000).toFixed(2));
      const portfolioRosi = Math.round(opt.portfolio_rosi_percentage ?? opt.portfolio_aggregate_rosi ?? (committedCr > 0 ? ((reductionCr - committedCr) / committedCr) * 100 : 0));

      const frontier = (curves.data_points || []).map((pt) => ({
        investment: Number((pt.cumulative_investment / 10000000).toFixed(2)),
        riskReduction: Number((pt.cumulative_risk_reduction / 10000000).toFixed(2)),
        eal: Number((pt.residual_eal / 10000000).toFixed(2)),
        rosi: Math.round(pt.marginal_rosi_pct || 0),
        controlAdded: pt.control_name || '',
      }));

      const initiatives = (controls || []).map((c, idx) => {
        const isSelected = (opt.selected_controls || []).some((sc) => sc.id === c.id);
        const costCr = Number((c.annual_cost / 10000000).toFixed(2));
        const reductionCrItem = Number(((c.risk_reduction || 0) / 10000000).toFixed(2));
        const rosiPct = c.rosi ? Math.round(c.rosi.rosi_percentage) : (costCr > 0 ? Math.round(((reductionCrItem - costCr) / costCr) * 100) : 0);
        const paybackMonths = reductionCrItem > 0 ? ((costCr / reductionCrItem) * 12).toFixed(1) + ' Months' : '< 1 Month';
        return {
          id: c.id,
          priorityRank: idx + 1,
          name: c.name,
          title: c.name,
          domain: c.target_asset_or_risk || 'Enterprise Defense',
          targetAsset: c.target_asset_or_risk || 'ENTERPRISE',
          cost: costCr,
          riskReduction: reductionCrItem,
          effectiveness: Math.round((c.effectiveness || 0.5) * 100),
          rosi: rosiPct,
          paybackPeriod: paybackMonths,
          status: isSelected ? 'APPROVED_FOR_BUDGET' : 'UNDER_REVIEW',
          description: c.description || '',
        };
      });

      return {
        totalBudget: totalBudgetCr,
        allocatedBudget: committedCr,
        portfolioRosi: portfolioRosi,
        totalRiskReduction: reductionCr,
        baselineEal: baselineEalCr,
        residualEal: residualEalCr,
        currentRiskScore: 71,
        projectedRiskScore: Math.max(15, Math.round(71 - (reductionCr / (baselineEalCr || 10)) * 40)),
        efficientFrontier: frontier.length > 0 ? frontier : [
          { investment: 0, riskReduction: 0, eal: baselineEalCr, rosi: 0 },
          { investment: committedCr, riskReduction: reductionCr, eal: residualEalCr, rosi: portfolioRosi }
        ],
        recommendedInitiatives: initiatives,
        topCandidateControls: initiatives,
        selectedControls: opt.selected_controls || [],
        unselectedControls: opt.unselected_controls || [],
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
    const budgetValue = typeof totalBudget === 'number' && totalBudget < 1000 
      ? totalBudget * 10000000 
      : totalBudget;
    const response = await apiClient.post('/investment/optimize', { total_budget: budgetValue });
    return response.data;
  },
  getControls: async () => {
    const response = await apiClient.get('/investment/controls');
    return response.data;
  },
};

export default investmentApi;
