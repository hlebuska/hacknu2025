// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiConfig = {
  baseUrl: API_URL,
  endpoints: {
    health: `${API_URL}/health`,
  },
};

export default apiConfig;
