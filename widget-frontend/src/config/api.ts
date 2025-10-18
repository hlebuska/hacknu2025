// API Configuration
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";

export const apiConfig = {
  baseUrl: API_URL,
  wsUrl: WS_URL,
  endpoints: {
    health: `${API_URL}/health`,
    chatWs: (applicationId: string) => `${WS_URL}/ws/chat/${applicationId}`,
  },
};

export default apiConfig;
