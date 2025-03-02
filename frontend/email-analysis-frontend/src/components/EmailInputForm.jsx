// src/components/EmailInputForm.jsx
import React, { useState } from 'react';
import { TextField, Button, Typography, Paper, Grid, IconButton } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

const EmailInputForm = ({ onSubmit, loading }) => {
  const [emailPairs, setEmailPairs] = useState([
    { id: 1, question: '', answer: '' }
  ]);

  const handleAddPair = () => {
    const newId = emailPairs.length > 0 
      ? Math.max(...emailPairs.map(pair => pair.id)) + 1 
      : 1;
    setEmailPairs([...emailPairs, { id: newId, question: '', answer: '' }]);
  };

  const handleRemovePair = (id) => {
    if (emailPairs.length <= 1) return; // Keep at least one pair
    setEmailPairs(emailPairs.filter(pair => pair.id !== id));
  };

  const handleChange = (id, field, value) => {
    setEmailPairs(emailPairs.map(pair => 
      pair.id === id ? { ...pair, [field]: value } : pair
    ));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(emailPairs);
  };

  return (
    <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Input Your Email Question-Answer Pairs
      </Typography>
      <Typography variant="body1" gutterBottom color="text.secondary">
        Please provide 15 email pairs to help us analyze your writing style.
      </Typography>
      
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
              disabled={emailPairs.length < 5 || loading}
            >
              {loading ? 'Analyzing...' : 'Submit for Analysis'}
            </Button>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default EmailInputForm;