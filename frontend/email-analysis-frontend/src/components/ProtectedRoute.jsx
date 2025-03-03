import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

// Component to protect routes that require authentication
const ProtectedRoute = ({ children }) => {
  const { currentUser, isLoading } = useAuth();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  // Render the protected content if authenticated
  return children;
};

export default ProtectedRoute;