import apiClient from './client';

export const riskApi = {
  getQuantitativeModeling: async () => {
    const response = await apiClient.get('/risk');
    return response.data;
  },
  runMonteCarlo: async (iterations = 50000, confidence = 95) => {
    const response = await apiClient.post('/risk/monte-carlo', { iterations, confidence });
    return response.data;
  },
  getStressScenarios: async () => {
    const response = await apiClient.get('/risk/scenarios');
    return response.data;
  }
};

export default riskApi;
