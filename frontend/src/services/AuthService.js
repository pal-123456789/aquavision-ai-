import axios from './api';

const AuthService = {
  register: async (userData) => {
    try {
      const response = await axios.post('/api/auth/register', userData);
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Registration failed';
    }
  },

  login: async (credentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials);
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Login failed';
    }
  },

  logout: async () => {
    try {
      await axios.post('/api/auth/logout');
      return true;
    } catch (error) {
      console.error('Logout failed:', error);
      return false;
    }
  },

  getCurrentUser: async () => {
    try {
      const response = await axios.get('/api/auth/me');
      return response.data;
    } catch (error) {
      return null;
    }
  },

  forgotPassword: async (email) => {
    try {
      const response = await axios.post('/api/auth/forgot-password', { email });
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Password reset failed';
    }
  },

  resetPassword: async (token, newPassword) => {
    try {
      const response = await axios.post('/api/auth/reset-password', {
        token,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Password reset failed';
    }
  }
};

export default AuthService;