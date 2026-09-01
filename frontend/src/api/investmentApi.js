import apiClient from './client';

export const investmentApi = {
  getControls: async () => {
    try {
      const response = await apiClient.get('/investment/controls');
      return response.data;
    } catch {
      const fallbackRes = await apiClient.get('/controls');
      return fallbackRes.data;
    }
  },
  getCurves: async (budget = null, enterpriseEal = null) => {
    const params = {};
    if (budget != null) params.budget = budget;
    if (enterpriseEal != null) params.enterprise_eal = enterpriseEal;
    const response = await apiClient.get('/investment/curves', { params });
    return response.data;
  },
  optimizeBudget: async (totalBudget, totalEnterpriseEal = null) => {
    try {
      // First try P5 dedicated knapsack endpoint
      const response = await apiClient.post('/investment/optimize', {
        total_budget: Number(totalBudget),
        total_enterprise_eal: totalEnterpriseEal ? Number(totalEnterpriseEal) : undefined,
      });
      return response.data;
    } catch {
      // Fallback to root platform investments/optimize endpoint
      const res = await apiClient.post('/investments/optimize', {
        budget: Number(totalBudget),
      });
      return {
        total_budget: res.data.budget,
        total_investment: Number(totalBudget) - Number(res.data.remaining_budget),
        remaining_budget: res.data.remaining_budget,
        total_risk_reduction: res.data.projected_risk_reduction,
        selected_controls: res.data.selected_investment_ids || [],
        portfolio_rosi_percentage: null,
      };
    }
  },
  calculateRosi: async (baselineEal, effectiveness, annualCost, controlName = 'Custom Control') => {
    const response = await apiClient.post('/investment/rosi', null, {
      params: {
        baseline_eal: baselineEal,
        effectiveness,
        annual_cost: annualCost,
        control_name: controlName,
      },
    });
    return response.data;
  },
};

export default investmentApi;
