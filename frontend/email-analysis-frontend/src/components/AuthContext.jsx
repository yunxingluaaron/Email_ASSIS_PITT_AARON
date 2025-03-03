import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';

// Create the auth context
const AuthContext = createContext();

// Custom hook to use the auth context
export const useAuth = () => useContext(AuthContext);

// Provider component
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = 'http://localhost:5000'; // Define your Flask backend URL

  // Setup axios default headers for authentication
  useEffect(() => {
    const userId = localStorage.getItem('userId');
    const sessionToken = localStorage.getItem('sessionToken');
    
    if (userId && sessionToken) {
      axios.defaults.headers.common['X-User-ID'] = userId;
      axios.defaults.headers.common['X-Session-Token'] = sessionToken;
    }
  }, [currentUser]);

  // Check session validity on mount
  useEffect(() => {
    const checkSession = async () => {
      const userId = localStorage.getItem('userId');
      const sessionToken = localStorage.getItem('sessionToken');
      const userEmail = localStorage.getItem('userEmail');
  
      if (userId && sessionToken) {
        try {
          // Verify the session
          const response = await axios.post(`${API_URL}/api/auth/verify-session`, {
            userId,
            sessionToken
          });
          
          if (response.data.success) {
            setCurrentUser({
              id: userId,
              email: userEmail
            });
          } else {
            // Session invalid, clear storage
            logout();
          }
        } catch (err) {
          console.error('Session verification error:', err);
          setError('Session verification failed');
          logout();
        }
      }
      
      setIsLoading(false);
    };
    
    checkSession();
  }, []);

  // Login function
  const login = async (email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        email,
        password
      });
      
      if (response.data.success) {
        localStorage.setItem('userId', response.data.userId);
        localStorage.setItem('userEmail', response.data.email);
        localStorage.setItem('sessionToken', response.data.sessionToken);
        
        setCurrentUser({
          id: response.data.userId,
          email: response.data.email
        });
        
        return { success: true };
      } else {
        setError(response.data.message || 'Login failed');
        return { success: false, error: response.data.message };
      }
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Login failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  // Register function
  const register = async (email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.post(`${API_URL}/api/auth/register`, {
        email,
        password
      });
      
      if (response.data.success) {
        localStorage.setItem('userId', response.data.userId);
        localStorage.setItem('userEmail', response.data.email);
        localStorage.setItem('sessionToken', response.data.sessionToken);
        
        setCurrentUser({
          id: response.data.userId,
          email: response.data.email
        });
        
        return { success: true };
      } else {
        setError(response.data.message || 'Registration failed');
        return { success: false, error: response.data.message };
      }
    } catch (err) {
      const errorMessage = err.response?.data?.message || 'Registration failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setIsLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    const userId = localStorage.getItem('userId');
    const sessionToken = localStorage.getItem('sessionToken');
    
    if (userId && sessionToken) {
      try {
        // Call logout API to clear the session on the server
        await axios.post('/api/auth/logout', {
          userId,
          sessionToken
        });
      } catch (err) {
        console.error('Logout error:', err);
      }
    }
    
    // Clear local storage and state
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('sessionToken');
    
    // Clear axios headers
    delete axios.defaults.headers.common['X-User-ID'];
    delete axios.defaults.headers.common['X-Session-Token'];
    
    setCurrentUser(null);
  };

  // Value object to be provided by the context
  const value = {
    currentUser,
    isLoading,
    error,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;