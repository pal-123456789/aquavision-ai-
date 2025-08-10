import axios from './api';

const AnalysisService = {
  detectAlgae: async (lat, lon) => {
    try {
      const response = await axios.get('/api/analysis/detect', {
        params: { lat, lon }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Detection failed';
    }
  },

  predictAlgae: async (lat, lon) => {
    try {
      const response = await axios.get('/api/analysis/predict', {
        params: { lat, lon }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Prediction failed';
    }
  },

  getHistory: async (page = 1, perPage = 10) => {
    try {
      const response = await axios.get('/api/analysis/history', {
        params: { page, per_page: perPage }
      });
      return response.data;
    } catch (error) {
      throw error.response?.data?.error || 'Failed to fetch history';
    }
  }
};

export default AnalysisService;