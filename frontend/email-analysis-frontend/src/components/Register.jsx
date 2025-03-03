import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../App.css';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState('');
  const navigate = useNavigate();
  
  const API_URL = 'http://localhost:5000'; // Define your Flask backend URL

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setDebugInfo('');
    setIsLoading(true);
    
    // Validate inputs
    if (!email || !password || !confirmPassword) {
      setError('All fields are required');
      setIsLoading(false);
      return;
    }
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setIsLoading(false);
      return;
    }
    
    const userData = {
      email,
      password
    };
    
    setDebugInfo(`Attempting to register with email: ${email}`);
    
    try {
      // Try with absolute URL to Flask backend
      setDebugInfo(debugInfo + '\nAttempting to connect to: ' + `${API_URL}/api/auth/register`);
      
      const response = await axios.post(`${API_URL}/api/auth/register`, userData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      setDebugInfo(debugInfo + '\nResponse received: ' + JSON.stringify(response.data));
      
      if (response.data.success) {
        // Store user data in localStorage
        localStorage.setItem('userId', response.data.userId);
        localStorage.setItem('userEmail', response.data.email);
        localStorage.setItem('sessionToken', response.data.sessionToken);
        
        // Redirect to dashboard
        navigate('/dashboard');
      } else {
        setError(response.data.message || 'Registration failed');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setDebugInfo(debugInfo + '\nError details: ' + 
                  '\nStatus: ' + (err.response?.status || 'No status') + 
                  '\nMessage: ' + err.message +
                  '\nResponse data: ' + JSON.stringify(err.response?.data || 'No data'));
      
      setError(err.response?.data?.message || 'An error occurred during registration');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create Account</h2>
        
        {error && <div className="error-message">{error}</div>}
        {debugInfo && (
          <div style={{ background: '#f8f9fa', padding: '10px', margin: '10px 0', borderRadius: '4px', fontSize: '12px' }}>
            <strong>Debug Info:</strong>
            <pre>{debugInfo}</pre>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          {/* Form fields remain the same */}
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a password"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirm-password">Confirm Password</label>
            <input
              type="password"
              id="confirm-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              required
            />
          </div>
          
          <button
            type="submit"
            className="submit-button"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Register'}
          </button>
        </form>
        
        <div className="auth-footer">
          <p>Already have an account? <a href="/login">Login</a></p>
        </div>
      </div>
    </div>
  );
};

export default Register;