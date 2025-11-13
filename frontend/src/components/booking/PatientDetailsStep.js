import React from 'react';
import {
  Box,
  Button,
  Typography,
  TextField,
  Grid,
  MenuItem,
} from '@mui/material';
import { ArrowBack, ArrowForward } from '@mui/icons-material';

function PatientDetailsStep({ data, onChange, onNext, onBack }) {
  const handleChange = (field) => (event) => {
    onChange({ [field]: event.target.value });
  };

  const isValid = () => {
    return data.patientName && data.patientPhone;
  };

  const handleNext = () => {
    if (isValid()) {
      onNext();
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Your Details
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Please provide your information to complete the booking
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <TextField
            required
            fullWidth
            label="Full Name"
            value={data.patientName}
            onChange={handleChange('patientName')}
            placeholder="John Doe"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            required
            fullWidth
            label="Phone Number"
            value={data.patientPhone}
            onChange={handleChange('patientPhone')}
            placeholder="+1234567890"
            helperText="Include country code"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Email Address"
            type="email"
            value={data.patientEmail}
            onChange={handleChange('patientEmail')}
            placeholder="john@example.com"
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Age"
            type="number"
            value={data.patientAge}
            onChange={handleChange('patientAge')}
            inputProps={{ min: 0, max: 150 }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            select
            fullWidth
            label="Gender"
            value={data.patientGender}
            onChange={handleChange('patientGender')}
          >
            <MenuItem value="">Select Gender</MenuItem>
            <MenuItem value="male">Male</MenuItem>
            <MenuItem value="female">Female</MenuItem>
            <MenuItem value="other">Other</MenuItem>
          </TextField>
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Additional Notes (Optional)"
            value={data.notes}
            onChange={handleChange('notes')}
            placeholder="Any additional information you'd like to share..."
          />
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
        >
          Back
        </Button>
        <Button
          variant="contained"
          endIcon={<ArrowForward />}
          onClick={handleNext}
          disabled={!isValid()}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}

export default PatientDetailsStep;
