import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';
import EmailInputForm from './EmailInputForm';
import StyleAnalysisResults from './StyleAnalysisResults';
import SyntheticEmailReview from './SyntheticEmailReview';
import EmailGenerator from './EmailGenerator';
import '../App.css';

const Dashboard = () => {
  const { currentUser, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('submit');
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasStyleProfile, setHasStyleProfile] = useState(false);
  const [styleProfileSaved, setStyleProfileSaved] = useState(false);

  // Fetch user data on component mount
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/user-data?userId=${currentUser.id}`);
        setUserData(response.data);
        
        // Check if user has approved synthetic emails
        const hasApprovedEmails = response.data.syntheticEmails && 
          response.data.syntheticEmails.some(email => email.approved);
        
        setHasStyleProfile(hasApprovedEmails);
      } catch (err) {
        console.error('Error fetching user data:', err);
        setError('Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) {
      fetchUserData();
    }
  }, [currentUser]);

  const handleLogout = async () => {
    await logout();
  };

  const handleSaveStyleProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/save-style-profile', {
        userId: currentUser.id
      });
      
      if (response.data.success) {
        setStyleProfileSaved(true);
        setTimeout(() => setStyleProfileSaved(false), 3000); // Hide message after 3 seconds
      } else {
        setError(response.data.message || 'Failed to save style profile');
      }
    } catch (err) {
      console.error('Error saving style profile:', err);
      setError('Failed to save style profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !userData) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading your data...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Email Style Analyzer</h1>
        <div className="user-info">
          <span className="user-email">{currentUser?.email}</span>
          <button className="logout-button" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <aside className="dashboard-sidebar">
          <div 
            className={`sidebar-item ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            Submit Emails
          </div>
          {userData && userData.styleAnalysis && (
            <div 
              className={`sidebar-item ${activeTab === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveTab('analysis')}
            >
              Style Analysis
            </div>
          )}
          {userData && userData.syntheticEmails && userData.syntheticEmails.length > 0 && (
            <div 
              className={`sidebar-item ${activeTab === 'review' ? 'active' : ''}`}
              onClick={() => setActiveTab('review')}
            >
              Review Synthetic Emails
            </div>
          )}
          <div 
            className={`sidebar-item ${activeTab === 'generate' ? 'active' : ''}`}
            onClick={() => setActiveTab('generate')}
          >
            Generate New Email
          </div>
          {hasStyleProfile && (
            <div 
              className={`sidebar-item ${activeTab === 'profile' ? 'active' : ''}`}
              onClick={() => setActiveTab('profile')}
            >
              Style Profile
            </div>
          )}
        </aside>

        <main className="dashboard-main">
          {error && (
            <div className="error-message">
              {error}
              <button onClick={() => setError(null)}>×</button>
            </div>
          )}
          
          {styleProfileSaved && (
            <div className="success-message">
              Style profile saved successfully!
            </div>
          )}

          {activeTab === 'submit' && (
            <div className="dashboard-section">
              <h2>Submit Your Emails for Analysis</h2>
              <EmailInputForm userId={currentUser.id} onSuccess={() => setActiveTab('analysis')} />
            </div>
          )}

          {activeTab === 'analysis' && userData?.styleAnalysis && (
            <div className="dashboard-section">
              <h2>Writing Style Analysis</h2>
              <StyleAnalysisResults analysisData={userData.styleAnalysis} />
            </div>
          )}

          {activeTab === 'review' && userData?.syntheticEmails && (
            <div className="dashboard-section">
              <h2>Review Synthetic Emails</h2>
              <p>Review and provide feedback on generated emails that match your writing style.</p>
              <SyntheticEmailReview 
                emails={userData.syntheticEmails} 
                userId={currentUser.id} 
              />
              
              {hasStyleProfile && (
                <div className="save-profile-section">
                  <p>Save your approved emails as your permanent style profile for future email generation.</p>
                  <button 
                    className="save-profile-button"
                    onClick={handleSaveStyleProfile}
                    disabled={loading}
                  >
                    {loading ? 'Saving...' : 'Save Style Profile'}
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'generate' && (
            <div className="dashboard-section">
              <h2>Generate New Email</h2>
              <p>Generate a new email based on your writing style.</p>
              <EmailGenerator userId={currentUser.id} />
            </div>
          )}

          {activeTab === 'profile' && hasStyleProfile && (
            <div className="dashboard-section">
              <h2>Style Profile Management</h2>
              <p>Your style profile is used to generate emails that match your unique writing style.</p>
              
              <div className="profile-status">
                <div className="status-indicator">
                  <span className="status-badge active">Active</span>
                </div>
                <p>Your style profile is currently active and will be used for all email generation.</p>
              </div>
              
              <div className="profile-actions">
                <button 
                  className="save-profile-button"
                  onClick={handleSaveStyleProfile}
                  disabled={loading}
                >
                  {loading ? 'Updating...' : 'Update Style Profile'}
                </button>
                <p className="profile-help">
                  To update your style profile, review and approve synthetic emails, then click "Update Style Profile"
                </p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;