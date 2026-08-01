import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response Interceptor to handle errors globally
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorMsg = error.response?.data?.detail || error.message || 'An error occurred';
    logger.error('API Error:', errorMsg);
    return Promise.reject(new Error(errorMsg));
  }
);

const logger = {
  error: (...args) => console.error('[API Error]', ...args),
};

export default apiClient;
