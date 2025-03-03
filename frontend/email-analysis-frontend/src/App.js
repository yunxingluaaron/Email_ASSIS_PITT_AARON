import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './components/AuthContext';
import Navbar from './components/Navbar';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import ProtectedRoute from './components/ProtectedRoute';
import EmailInputForm from './components/EmailInputForm';
import StyleAnalysisResults from './components/StyleAnalysisResults';
import SyntheticEmailReview from './components/SyntheticEmailReview';
import EmailGenerator from './components/EmailGenerator';
import CombinedAnalysisView from './components/CombinedAnalysisView';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Navbar />
          <div className="app-container">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected routes */}
              <Route 
                path="/dashboard" 
                element={
                  <ProtectedRoute>
                    <Dashboard />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/submit-emails" 
                element={
                  <ProtectedRoute>
                    <EmailInputForm />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/style-analysis" 
                element={
                  <ProtectedRoute>
                    <StyleAnalysisResults />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/review-emails" 
                element={
                  <ProtectedRoute>
                    <SyntheticEmailReview />
                  </ProtectedRoute>
                } 
              />
              
              <Route 
                path="/generate-email" 
                element={
                  <ProtectedRoute>
                    <EmailGenerator />
                  </ProtectedRoute>
                } 
              />
              
              {/* Default redirect */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </div>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;