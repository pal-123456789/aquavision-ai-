import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// Response interceptor to handle errors
api.interceptors.response.use(response => response, error => {
  if (error.response && error.response.status === 401) {
    // Handle unauthorized access
    localStorage.removeItem('authToken');
    window.location.reload();
  }
  return Promise.reject(error);
});

export default api;