// src/components/StyleAnalysisResults.jsx
import React from 'react';
import { Typography, Paper, Accordion, AccordionSummary, AccordionDetails, Chip, Box } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const StyleAnalysisResults = ({ styleAnalysis }) => {
  if (!styleAnalysis) return null;

  return (
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
      
      {styleAnalysis.categories.map((category, index) => (
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
    </Paper>
  );
};

export default StyleAnalysisResults;