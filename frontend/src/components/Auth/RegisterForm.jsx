import { useState } from 'react';
import { Alert, Button, Form, ProgressBar } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import AuthService from '../../services/AuthService';

const RegisterForm = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const calculatePasswordStrength = (password) => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 25;
    if (/[\W_]/.test(password)) strength += 25;
    return strength;
  };

  const handlePasswordChange = (e) => {
    const pwd = e.target.value;
    setPassword(pwd);
    setPasswordStrength(calculatePasswordStrength(pwd));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (passwordStrength < 75) {
      setError('Password is too weak');
      return;
    }
    
    setError('');
    setLoading(true);

    try {
      const response = await AuthService.register({ name, email, password });
      toast.success('Registration successful!');
      navigate('/');
    } catch (error) {
      setError(error.message || 'Registration failed');
      toast.error(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrengthVariant = () => {
    if (passwordStrength < 40) return 'danger';
    if (passwordStrength < 70) return 'warning';
    return 'success';
  };

  return (
    <div className="auth-form-container">
      <h2 className="text-center mb-4">Create Your Account</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3" controlId="formName">
          <Form.Label>Full Name</Form.Label>
          <Form.Control 
            type="text" 
            placeholder="Enter your name" 
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </Form.Group>

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
              onChange={handlePasswordChange}
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
          {password && (
            <>
              <ProgressBar 
                className="mt-2" 
                now={passwordStrength} 
                variant={getPasswordStrengthVariant()} 
              />
              <small className="text-muted">
                Password strength: 
                <span className={`ms-1 fw-bold text-${getPasswordStrengthVariant()}`}>
                  {passwordStrength < 40 ? 'Weak' : passwordStrength < 70 ? 'Medium' : 'Strong'}
                </span>
              </small>
            </>
          )}
        </Form.Group>

        <Form.Group className="mb-3" controlId="formConfirmPassword">
          <Form.Label>Confirm Password</Form.Label>
          <Form.Control 
            type="password" 
            placeholder="Confirm Password" 
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />
        </Form.Group>

        <Form.Group className="mb-3" controlId="formTerms">
          <Form.Check 
            type="checkbox"
            label={
              <>
                I agree to the <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
              </>
            }
            required
          />
        </Form.Group>

        <div className="d-grid mb-3">
          <Button variant="primary" type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                Creating account...
              </>
            ) : 'Create Account'}
          </Button>
        </div>
      </Form>
      
      <div className="text-center mt-4">
        <p className="text-muted">
          Already have an account? <a href="/login" className="text-decoration-none">Sign in</a>
        </p>
      </div>
    </div>
  );
};

export default RegisterForm;