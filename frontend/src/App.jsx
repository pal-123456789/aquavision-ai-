import { useEffect, useState } from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './App.css';
import Navbar from './components/Navbar';
import ApiDocs from './pages/ApiDocs';
import Dashboard from './pages/Dashboard';
import HistoryPage from './pages/HistoryPage';
import AuthService from './services/AuthService';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await AuthService.getCurrentUser();
        if (userData) {
          setUser(userData.user);
          localStorage.setItem('authToken', userData.user.api_key);
        }
      } catch (error) {
        console.log('User not authenticated');
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  const handleLogin = (userData) => {
    setUser(userData.user);
    localStorage.setItem('authToken', userData.user.api_key);
  };

  const handleLogout = async () => {
    await AuthService.logout();
    setUser(null);
    localStorage.removeItem('authToken');
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Navbar user={user} onLogout={handleLogout} />
      <div className="container-fluid p-0 main-content">
        <Routes>
          <Route path="/" element={<Dashboard user={user} />} />
          <Route path="/history" element={<HistoryPage user={user} />} />
          <Route path="/api-docs" element={<ApiDocs />} />
        </Routes>
      </div>
      <ToastContainer position="bottom-right" />
    </Router>
  );
}

export default App;