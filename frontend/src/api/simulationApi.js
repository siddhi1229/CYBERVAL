import apiClient from './client';

export const simulationApi = {
  getControls: async () => {
    const response = await apiClient.get('/controls');
    return response.data;
  },
  runSimulation: async (budget = 0, iterations = 1000) => {
    const response = await apiClient.post('/simulation/run', {
      budget: Number(budget),
      iterations: Number(iterations),
    });
    return response.data;
  },
};

export default simulationApi;
