// src/components/EmailInputForm.jsx
import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Grid, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import axios from 'axios';
import { useAuth } from './AuthContext';
import { useNavigate } from 'react-router-dom';

const EmailInputForm = ({ onSubmit, loading }) => {
  const [emailPairs, setEmailPairs] = useState([
    { id: 1, question: '', answer: '' }
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const API_URL = 'http://localhost:5000'; 

  const handleAddPair = () => {
    const newId = emailPairs.length > 0
       ? Math.max(...emailPairs.map(pair => pair.id)) + 1
       : 1;
    setEmailPairs([...emailPairs, { id: newId, question: '', answer: '' }]);
  };

  const handleRemovePair = (id) => {
    if (emailPairs.length <= 1) return;
    setEmailPairs(emailPairs.filter(pair => pair.id !== id));
  };

  const handleChange = (id, field, value) => {
    setEmailPairs(emailPairs.map(pair =>
       pair.id === id ? { ...pair, [field]: value } : pair
    ));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (typeof onSubmit === 'function') {
      onSubmit(emailPairs);
      return;
    }
    
    try {
      setIsSubmitting(true);
      setSubmitError('');
      
      // Format data to match exactly what backend expects
      const formattedData = emailPairs.map(pair => ({
        question: pair.question,
        answer: pair.answer
      }));
  
      // Get user ID from localStorage
      const userId = localStorage.getItem('userId');
      
      // Notice the endpoint matches exactly your Flask route
      const response = await axios.post(
        `${API_URL}/api/submit-emails`, 
        {
          userId: userId,
          emailPairs: formattedData // Changed back to 'emailPairs' to match your backend
        }
      );
      
      if (response.data && !response.data.error) {
        navigate('/style-analysis'); // This route now shows the combined view
      } else {
        setSubmitError(response.data.error || 'Failed to submit emails');
      }
    } catch (error) {
      console.error('Error submitting emails:', error);
      
      if (error.response) {
        console.log('Server responded with:', error.response.status, error.response.data);
        setSubmitError(error.response.data.error || 'Server error. Please try again.');
      } else if (error.request) {
        console.log('No response received:', error.request);
        setSubmitError('Cannot connect to server. Please check your connection and try again.');
      } else {
        setSubmitError('Error setting up request: ' + error.message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Input Your Email Question-Answer Pairs
      </Typography>
      <Typography variant="body1" gutterBottom color="text.secondary">
        Please provide at least 5 email pairs to help us analyze your writing style.
      </Typography>
      
      {submitError && (
        <Typography variant="body2" color="error" sx={{ mt: 2, mb: 2 }}>
          {submitError}
        </Typography>
      )}
      
      <form onSubmit={handleSubmit}>
        {emailPairs.map((pair, index) => (
          <Grid container spacing={2} key={pair.id} sx={{ mb: 3 }}>
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom>
                Email Pair #{index + 1}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Email Question/Context"
                value={pair.question}
                onChange={(e) => handleChange(pair.id, 'question', e.target.value)}
                placeholder="What was the email about? What prompted your response?"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={4}
                label="Your Email Response"
                value={pair.answer}
                onChange={(e) => handleChange(pair.id, 'answer', e.target.value)}
                placeholder="Paste your actual email response here"
                required
              />
            </Grid>
            <Grid item xs={12} textAlign="right">
              <IconButton
                 color="error"
                 onClick={() => handleRemovePair(pair.id)}
                disabled={emailPairs.length <= 1}
              >
                <DeleteIcon />
              </IconButton>
            </Grid>
          </Grid>
        ))}
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Button
              startIcon={<AddIcon />}
              onClick={handleAddPair}
              fullWidth
              variant="outlined"
            >
              Add Another Email Pair
            </Button>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              disabled={(emailPairs.length < 2) || loading || isSubmitting}
            >
              {loading || isSubmitting ? 'Analyzing...' : 'Submit for Analysis'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

EmailInputForm.defaultProps = {
  onSubmit: null,
  loading: false
};

export default EmailInputForm;