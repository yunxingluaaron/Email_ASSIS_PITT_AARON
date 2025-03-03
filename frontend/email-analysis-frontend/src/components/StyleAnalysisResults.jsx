// src/components/StyleAnalysisResults.jsx
import React, { useState, useEffect } from 'react';
import { 
  Typography, Paper, Accordion, AccordionSummary, AccordionDetails, 
  Chip, Box, CircularProgress, Button, Snackbar, Alert 
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import axios from 'axios';
import SyntheticEmailReview from './SyntheticEmailReview';

const StyleAnalysisResults = () => {
  const [styleAnalysis, setStyleAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syntheticEmails, setSyntheticEmails] = useState(null);
  const [generatingEmails, setGeneratingEmails] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState('info');
  
  const API_URL = 'http://localhost:5000';
  
  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        const userId = localStorage.getItem('userId');
        const sessionToken = localStorage.getItem('sessionToken');
        
        console.log('Attempting to fetch from:', `${API_URL}/api/style-analysis`);
        console.log('Headers:', {
          'X-User-ID': userId,
          'X-Session-Token': sessionToken
        });
        
        const config = {
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId,
            'X-Session-Token': sessionToken
          }
        };
        
        const response = await axios.get(
          `${API_URL}/api/style-analysis`,
          config
        );
        
        console.log('Response received:', response.data);
        setStyleAnalysis(response.data);
      } catch (error) {
        console.error('Error details:', error);
        
        if (error.response) {
          // Server responded with a status code outside of 2xx range
          console.error('Response status:', error.response.status);
          console.error('Response data:', error.response.data);
        } else if (error.request) {
          // Request was made but no response received
          console.error('No response received from server');
        } else {
          // Something else happened
          console.error('Error message:', error.message);
        }
        
        setError('Could not load your style analysis. Please check console for details.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalysisData();
  }, []);

  const handleGenerateSyntheticEmails = async () => {
    setGeneratingEmails(true);
    setSnackbarMessage('Generating synthetic emails based on your style...');
    setSnackbarSeverity('info');
    setSnackbarOpen(true);
    
    try {
      const userId = localStorage.getItem('userId');
      
      // Use fetch instead of axios for simplicity
      const response = await fetch(`${API_URL}/api/synthetic-emails`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId
        },
        // This matches your CORS settings
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Synthetic emails response:', data);
      setSyntheticEmails(data);
      
      setSnackbarMessage('Synthetic emails generated successfully!');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error generating synthetic emails:', error);
      setSnackbarMessage('Failed to generate synthetic emails: ' + error.message);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setGeneratingEmails(false);
    }
  };

  const handleEmailFeedback = async (feedbackData) => {
    try {
      const userId = localStorage.getItem('userId');
      
      // Add userId to the feedback data
      const data = {
        ...feedbackData,
        userId
      };
      
      console.log('Submitting email feedback:', data);
      
      const response = await axios.post(
        `${API_URL}/api/email-feedback`,
        data,
        {
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': userId
          }
        }
      );
      
      console.log('Feedback response:', response.data);
      
      // If response contains updated emails, update the state
      if (response.data.updatedEmails && feedbackData.category) {
        // Create a new synthetic emails object with the updated category
        const updatedSyntheticEmails = {
          ...syntheticEmails,
          [feedbackData.category]: response.data.updatedEmails
        };
        
        setSyntheticEmails(updatedSyntheticEmails);
      }
      
      setSnackbarMessage(
        feedbackData.isApproved 
          ? 'Email approved successfully!' 
          : 'Feedback submitted and email improved!'
      );
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error submitting feedback:', error);
      
      setSnackbarMessage('Failed to submit feedback. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    }
  };

  if (loading) {
    return (
      <Paper elevation={3} sx={{ p: 4, mb: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading your style analysis...
        </Typography>
      </Paper>
    );
  }
  
  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h5" component="h2" color="error" gutterBottom>
          Error Loading Analysis
        </Typography>
        <Typography variant="body1">
          {error}
        </Typography>
      </Paper>
    );
  }
  
  return (
    <>
      <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Your Email Style Analysis
        </Typography>
        
        <Typography variant="body1" paragraph>
          {styleAnalysis.overall_style_summary}
        </Typography>
        
        <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
          Style Categories
        </Typography>
        
        {styleAnalysis.categories && styleAnalysis.categories.map((category, index) => (
          <Accordion key={index} sx={{ mb: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography fontWeight="bold">{category.name}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography paragraph>{category.description}</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {category.key_characteristics.map((characteristic, i) => (
                  <Chip key={i} label={characteristic} color="primary" variant="outlined" />
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>
        ))}
        
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<AutoAwesomeIcon />}
            onClick={handleGenerateSyntheticEmails}
            disabled={generatingEmails}
            sx={{ minWidth: '250px' }}
          >
            {generatingEmails ? 'Generating...' : 'Generate Synthetic Emails'}
          </Button>
        </Box>
      </Paper>
      
      {/* Render the SyntheticEmailReview component if emails are available */}
      {syntheticEmails && (
        <SyntheticEmailReview 
          syntheticEmails={syntheticEmails} 
          onFeedback={handleEmailFeedback} 
        />
      )}
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default StyleAnalysisResults;