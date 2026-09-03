import apiClient from './client';

export const simulationApi = {
  getControls: async () => {
    try {
      const response = await apiClient.get('/controls');
      const controls = response.data || [];
      return controls.map((c) => ({
        id: `ctrl_${c.id}`,
        name: c.name,
        category: c.name.includes('Access') || c.name.includes('Authentication') ? 'Identity' : c.name.includes('Patch') ? 'Vulnerability' : 'Network',
        cost: Number((c.id * 0.4).toFixed(1)),
        riskReduction: Number(((c.effectiveness || 0.6) * 4.2).toFixed(1)),
        riskScoreImpact: -Math.round((c.effectiveness || 0.6) * 15),
        description: c.description || `Enterprise implementation of ${c.name}`,
        domain: 'Infrastructure & SecOps',
      }));
    } catch (e) {
      console.warn('Live simulation controls failed, re-throwing:', e);
      throw e;
    }
  },

  calculateScenario: async (enabledControlIds = []) => {
    try {
      const [controls, entRes] = await Promise.all([
        simulationApi.getControls(),
        apiClient.get('/risk/enterprise').catch(() => ({ data: {} })),
      ]);
      let totalCost = 0;
      let totalReduction = 0;
      let scoreDelta = 0;

      controls.forEach((ctrl) => {
        if (enabledControlIds.includes(ctrl.id)) {
          totalCost += ctrl.cost;
          totalReduction += ctrl.riskReduction;
          scoreDelta += ctrl.riskScoreImpact;
        }
      });

      const totalEalRaw = entRes.data?.total_expected_annual_loss;
      const baseEal = totalEalRaw ? Number((totalEalRaw / 10000000).toFixed(2)) : 54.69;
      const baseRisk = 74;
      const baseExposure = Number((baseEal * 3.37).toFixed(1));
      const baseP95 = Number((baseEal * 1.08).toFixed(1));

      const simulatedEal = Math.max(2.0, Number((baseEal - totalReduction).toFixed(2)));
      const simulatedScore = Math.max(15, Math.min(100, baseRisk + scoreDelta));
      const rosi = totalCost > 0 ? Number((((totalReduction - totalCost) / totalCost) * 100).toFixed(1)) : 0;

      return {
        before: {
          riskScore: baseRisk,
          eal: baseEal,
          financialExposure: baseExposure,
          p95Loss: baseP95,
        },
        after: {
          riskScore: simulatedScore,
          eal: simulatedEal,
          financialExposure: Number(Math.max(5.0, baseExposure - totalReduction * 2.5).toFixed(1)),
          p95Loss: Number(Math.max(2.0, baseP95 - totalReduction * 1.6).toFixed(1)),
        },
        cost: Number(totalCost.toFixed(2)),
        reduction: Number(totalReduction.toFixed(2)),
        rosi: rosi,
        enabledControlsCount: enabledControlIds.length,
        paybackMonths: totalReduction > 0 ? Number(((totalCost / totalReduction) * 12).toFixed(1)) : 0,
      };
    } catch (e) {
      console.warn('Live simulation calculation failed, re-throwing:', e);
      throw e;
    }
  },
};

export default simulationApi;
