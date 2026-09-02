import axios from 'axios';

// The Vite development proxy forwards /api to http://localhost:8000
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request Interceptor: attach authorization token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('cyberval_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: pass response or reject with backend error (no fake fallbacks)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log meaningful API error for diagnostics
    const endpoint = error.config?.url || 'Unknown endpoint';
    const status = error.response?.status || 'Network Error';
    console.error(`[CYBERVAL API Error] ${status} at ${endpoint}:`, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient;
