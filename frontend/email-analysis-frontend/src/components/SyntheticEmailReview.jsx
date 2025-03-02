// src/components/SyntheticEmailReview.jsx
import React, { useState } from 'react';
import { 
  Typography, Paper, Tabs, Tab, Box, Card, CardContent, 
  CardActions, Button, TextField, Rating, Dialog, 
  DialogTitle, DialogContent, DialogActions, Snackbar, Alert
} from '@mui/material';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';

const SyntheticEmailReview = ({ syntheticEmails, onFeedback }) => {
  const [categoryTab, setCategoryTab] = useState(0);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  if (!syntheticEmails || Object.keys(syntheticEmails).length === 0) return null;
  
  const categories = Object.keys(syntheticEmails);
  
  const handleTabChange = (event, newValue) => {
    setCategoryTab(newValue);
  };
  
  const handleApprove = (email, category) => {
    onFeedback({
      emailId: email.id,
      category,
      isApproved: true,
      rating: null,
      comments: null
    });
    setSnackbarMessage('Email approved!');
    setSnackbarOpen(true);
  };
  
  const handleImprove = (email, category) => {
    setSelectedEmail({ ...email, category });
    setRating(0);
    setFeedback('');
    setFeedbackDialogOpen(true);
  };
  
  const handleFeedbackSubmit = () => {
    onFeedback({
      emailId: selectedEmail.id,
      category: selectedEmail.category,
      isApproved: false,
      rating,
      comments: feedback
    });
    setFeedbackDialogOpen(false);
    setSnackbarMessage('Feedback submitted! Regenerating improved email...');
    setSnackbarOpen(true);
  };

  return (
    <Paper elevation={3} sx={{ p: 4, mb: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Review Synthetic Emails
      </Typography>
      
      <Typography variant="body1" paragraph>
        For each category, we've generated 10 sample emails that match your writing style. 
        Please review them and provide feedback.
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs
          value={categoryTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          {categories.map((category, index) => (
            <Tab label={category} key={index} />
          ))}
        </Tabs>
      </Box>
      
      <Box>
        {categories.map((category, index) => (
          <Box key={category} sx={{ display: categoryTab === index ? 'block' : 'none' }}>
            {syntheticEmails[category].map((email, emailIndex) => (
              <Card key={emailIndex} sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Sample {emailIndex + 1}
                  </Typography>
                  <Typography 
                    component="pre" 
                    sx={{ 
                      whiteSpace: 'pre-wrap', 
                      fontFamily: 'inherit',
                      backgroundColor: 'background.paper',
                      p: 2,
                      borderRadius: 1
                    }}
                  >
                    {email.content || email}
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button 
                    startIcon={<ThumbUpIcon />} 
                    variant="contained" 
                    color="success"
                    onClick={() => handleApprove(email, category)}
                  >
                    Approve
                  </Button>
                  <Button 
                    startIcon={<ThumbDownIcon />} 
                    variant="outlined" 
                    color="error"
                    onClick={() => handleImprove(email, category)}
                  >
                    Needs Improvement
                  </Button>
                </CardActions>
              </Card>
            ))}
          </Box>
        ))}
      </Box>
      
      {/* Feedback Dialog */}
      <Dialog open={feedbackDialogOpen} onClose={() => setFeedbackDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Provide Feedback</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3, mt: 1 }}>
            <Typography gutterBottom>How would you rate this email?</Typography>
            <Rating 
              value={rating} 
              onChange={(event, newValue) => setRating(newValue * 20)} 
              precision={0.5} 
              max={5}
            />
            <Typography variant="caption">
              Rating: {rating}/100
            </Typography>
          </Box>
          
          <TextField
            label="What needs improvement?"
            multiline
            rows={4}
            fullWidth
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Please provide specific feedback on how to improve this email to better match your style"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleFeedbackSubmit}
            variant="contained" 
            color="primary"
            disabled={!rating || !feedback}
          >
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity="success" 
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Paper>
  );
};

export default SyntheticEmailReview;