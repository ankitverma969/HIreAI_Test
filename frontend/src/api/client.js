import axios from 'axios';

const logger = {
  error: (...args) => console.error('[API Error]', ...args),
};

/** Reads the active backend URL from localStorage (set in Settings page). */
const getBaseURL = () =>
  localStorage.getItem('serverUrl') || 'http://localhost:8000';

const apiClient = axios.create({
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dynamically set baseURL before every request using the stored server URL
apiClient.interceptors.request.use((config) => {
  config.baseURL = getBaseURL();
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    config.headers = config.headers || {};
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

// Response Interceptor — unwrap data and handle errors globally
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorMsg =
      error.response?.data?.detail || error.message || 'An error occurred';
    logger.error('API Error:', errorMsg);
    return Promise.reject(new Error(errorMsg));
  }
);

export { getBaseURL };
export default apiClient;
