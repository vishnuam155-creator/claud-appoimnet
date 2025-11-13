import React from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
} from '@mui/material';
import { ArrowForward } from '@mui/icons-material';

function SymptomStep({ value, onChange, onNext }) {
  const handleNext = () => {
    if (value.trim()) {
      onNext();
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        What symptoms are you experiencing?
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Please describe your symptoms in detail to help us find the right doctor for you.
      </Typography>

      <TextField
        fullWidth
        multiline
        rows={4}
        label="Symptoms"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="e.g., I have been experiencing severe headaches and dizziness for the past week..."
        sx={{ mb: 3 }}
      />

      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          endIcon={<ArrowForward />}
          onClick={handleNext}
          disabled={!value.trim()}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}

export default SymptomStep;
