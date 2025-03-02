// src/App.jsx
import React, { useState, useEffect } from 'react';
import { 
  Container, Stepper, Step, StepLabel, 
  Box, Typography, CssBaseline, AppBar, Toolbar, 
  Button, Paper
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import EmailIcon from '@mui/icons-material/Email';
import EmailInputForm from './components/EmailInputForm';
import StyleAnalysisResults from './components/StyleAnalysisResults';
import SyntheticEmailReview from './components/SyntheticEmailReview';
import EmailGenerator from './components/EmailGenerator';
import { API_BASE_URL } from './config';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#f50057',
    },
  },
});

function App() {
  const [activeStep, setActiveStep] = useState(0);
  const [userId, setUserId] = useState(localStorage.getItem('userId') || null);
  const [loading, setLoading] = useState(false);
  const [styleAnalysis, setStyleAnalysis] = useState(null);
  const [syntheticEmails, setSyntheticEmails] = useState(null);
  const [generatedEmail, setGeneratedEmail] = useState(null);
  
  // Create a userId on first load if not exists
  useEffect(() => {
    if (!userId) {
      const newUserId = 'user_' + Math.random().toString(36).substring(2, 15);
      localStorage.setItem('userId', newUserId);
      setUserId(newUserId);
    }
    
    // Check if user has completed analysis
    const checkUserData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/user-data?userId=${userId}`);
        const data = await response.json();
        
        if (data.success && data.hasCompletedAnalysis) {
          setActiveStep(2); // Skip to email generation step
        }
      } catch (error) {
        console.error('Error checking user data:', error);
      }
    };
    
    if (userId) {
      checkUserData();
    }
  }, [userId]);
  
  const steps = [
    'Input Email Samples',
    'Review Style Analysis',
    'Generate Emails'
  ];
  
  const handleEmailSubmit = async (emailPairs) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/submit-emails`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          emailPairs
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStyleAnalysis(data.styleAnalysis);
        setSyntheticEmails(data.syntheticEmails);
        setActiveStep(1);
      }
    } catch (error) {
      console.error('Error submitting emails:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleEmailFeedback = async (feedbackData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/email-feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          ...feedbackData
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.improvedEmail) {
        // Update synthetic emails with the improved version
        setSyntheticEmails(prevEmails => {
          const category = feedbackData.category;
          const newEmails = { ...prevEmails };
          
          newEmails[category] = newEmails[category].map(email => 
            email.id === feedbackData.emailId 
              ? { ...email, content: data.improvedEmail, id: data.newEmailId }
              : email
          );
          
          return newEmails;
        });
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('An error occurred. Please try again.');
    }
  };
  
  const handleCompleteReview = () => {
    setActiveStep(2);
  };
  
  const handleGenerateEmail = async (emailData) => {
    setLoading(true);
    setGeneratedEmail(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId,
          ...emailData
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setGeneratedEmail(data.generatedEmail);
      }
    } catch (error) {
      console.error('Error generating email:', error);
      alert('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return <EmailInputForm onSubmit={handleEmailSubmit} loading={loading} />;
      case 1:
        return (
          <>
            <StyleAnalysisResults styleAnalysis={styleAnalysis} />
            <SyntheticEmailReview 
              syntheticEmails={syntheticEmails} 
              onFeedback={handleEmailFeedback} 
            />
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleCompleteReview}
              >
                Continue to Email Generation
              </Button>
            </Box>
          </>
        );
      case 2:
        return <EmailGenerator 
                onGenerate={handleGenerateEmail} 
                loading={loading} 
                generatedEmail={generatedEmail} 
              />;
      default:
        return <Typography>Unknown step</Typography>;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <EmailIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Email Assistant
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
        <Paper elevation={0} sx={{ p: 3, mb: 4 }}>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Paper>
        
        {renderStepContent()}
      </Container>
    </ThemeProvider>
  );
}

export default App;