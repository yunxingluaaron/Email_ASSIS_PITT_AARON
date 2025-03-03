// src/components/CombinedAnalysisView.jsx
import React, { useState, useEffect } from 'react';
import { Typography, Paper, Grid, Container, CircularProgress, Box } from '@mui/material';
import StyleAnalysisResults from './StyleAnalysisResults';
import SyntheticEmailReview from './SyntheticEmailReview';
import axios from 'axios';

const CombinedAnalysisView = () => {
  const [syntheticEmails, setSyntheticEmails] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const API_URL = 'http://localhost:5000';
  
  useEffect(() => {
    const fetchSyntheticEmails = async () => {
      try {
        const userId = localStorage.getItem('userId');
        const sessionToken = localStorage.getItem('sessionToken');
        
        const config = {
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId,
            'X-Session-Token': sessionToken
          }
        };
        
        const response = await axios.get(
          `${API_URL}/api/synthetic-emails`,
          config
        );
        
        console.log('Synthetic emails received:', response.data);
        setSyntheticEmails(response.data);
      } catch (error) {
        console.error('Error fetching synthetic emails:', error);
        
        if (error.response) {
          console.error('Response status:', error.response.status);
          console.error('Response data:', error.response.data);
        }
        
        setError('Could not load synthetic emails. Please check console for details.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSyntheticEmails();
  }, []);
  
  const handleEmailFeedback = async (feedbackData) => {
    try {
      const userId = localStorage.getItem('userId');
      const sessionToken = localStorage.getItem('sessionToken');
      
      const config = {
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
          'X-Session-Token': sessionToken
        }
      };
      
      const response = await axios.post(
        `${API_URL}/api/email-feedback`,
        {
          userId,
          ...feedbackData
        },
        config
      );
      
      // If we get improved emails back, update the state
      if (response.data && response.data.updatedEmails) {
        setSyntheticEmails(prev => {
          const updated = {...prev};
          updated[feedbackData.category] = response.data.updatedEmails;
          return updated;
        });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };
  
  const renderSyntheticEmailsSection = () => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', padding: 4 }}>
          <CircularProgress />
          <Typography variant="body1" sx={{ ml: 2 }}>
            Loading synthetic emails...
          </Typography>
        </Box>
      );
    }
    
    if (error) {
      return (
        <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
          <Typography variant="h6" component="h3" color="error" gutterBottom>
            Error Loading Synthetic Emails
          </Typography>
          <Typography variant="body1">{error}</Typography>
        </Paper>
      );
    }
    
    if (!syntheticEmails || Object.keys(syntheticEmails).length === 0) {
      return (
        <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
          <Typography variant="body1">
            No synthetic emails generated yet. The system is still analyzing your style.
          </Typography>
        </Paper>
      );
    }
    
    return (
      <SyntheticEmailReview 
        syntheticEmails={syntheticEmails} 
        onFeedback={handleEmailFeedback}
      />
    );
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4, mb: 3 }}>
        Your Writing Style Analysis
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <StyleAnalysisResults />
        </Grid>
        
        <Grid item xs={12}>
          <Typography variant="h4" component="h2" gutterBottom sx={{ mt: 2, mb: 2 }}>
            Generated Emails Based on Your Style
          </Typography>
          {renderSyntheticEmailsSection()}
        </Grid>
      </Grid>
    </Container>
  );
};

export default CombinedAnalysisView;