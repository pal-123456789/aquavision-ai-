import { useState } from 'react';
import { Alert, Button, Form } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import AuthService from '../../services/AuthService';

const LoginForm = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await AuthService.login({ email, password });
      toast.success('Login successful!');
      navigate('/');
    } catch (error) {
      setError(error.message || 'Login failed');
      toast.error(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <h2 className="text-center mb-4">Sign In to AquaVision</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="formEmail">
          <Form.Label>Email address</Form.Label>
          <Form.Control 
            type="email" 
            placeholder="Enter email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="formPassword">
          <Form.Label>Password</Form.Label>
          <div className="input-group">
            <Form.Control 
              type="password" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <button 
              className="btn btn-outline-secondary" 
              type="button"
              onClick={() => {
                const input = document.getElementById('formPassword');
                input.type = input.type === 'password' ? 'text' : 'password';
              }}
            >
              <i className="fas fa-eye"></i>
            </button>
          </div>
        </Form.Group>

        <div className="d-grid mb-3">
          <Button variant="primary" type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                Signing in...
              </>
            ) : 'Sign In'}
          </Button>
        </div>
        
        <div className="text-center">
          <a href="#" className="text-decoration-none">
            Forgot password?
          </a>
        </div>
      </Form>
      
      <div className="text-center mt-4">
        <p className="text-muted">
          Don't have an account? <a href="/register" className="text-decoration-none">Sign up</a>
        </p>
      </div>
    </div>
  );
};

export default LoginForm;