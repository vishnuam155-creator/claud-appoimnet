import React from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Grid,
  Divider,
  CircularProgress,
} from '@mui/material';
import { ArrowBack, CheckCircle } from '@mui/icons-material';
import { format } from 'date-fns';

function ConfirmationStep({ data, onBack, onSubmit, isLoading }) {
  const InfoRow = ({ label, value }) => (
    <Box sx={{ mb: 2 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body1" fontWeight={500}>
        {value}
      </Typography>
    </Box>
  );

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Confirm Your Appointment
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Please review your booking details before confirming
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Appointment Details
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <InfoRow label="Doctor" value={`Dr. ${data.doctor?.name}`} />
            <InfoRow label="Specialization" value={data.specialization?.name} />
            <InfoRow
              label="Date"
              value={format(new Date(data.date), 'EEEE, MMMM d, yyyy')}
            />
            <InfoRow label="Time" value={data.time} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <InfoRow label="Patient Name" value={data.patientName} />
            <InfoRow label="Phone" value={data.patientPhone} />
            {data.patientEmail && (
              <InfoRow label="Email" value={data.patientEmail} />
            )}
            {data.patientAge && (
              <InfoRow label="Age" value={`${data.patientAge} years`} />
            )}
          </Grid>
        </Grid>

        {data.symptoms && (
          <>
            <Divider sx={{ my: 2 }} />
            <InfoRow label="Symptoms" value={data.symptoms} />
          </>
        )}

        {data.notes && (
          <>
            <Divider sx={{ my: 2 }} />
            <InfoRow label="Additional Notes" value={data.notes} />
          </>
        )}
      </Paper>

      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          disabled={isLoading}
        >
          Back
        </Button>
        <Button
          variant="contained"
          size="large"
          startIcon={isLoading ? <CircularProgress size={20} /> : <CheckCircle />}
          onClick={onSubmit}
          disabled={isLoading}
        >
          {isLoading ? 'Confirming...' : 'Confirm Appointment'}
        </Button>
      </Box>
    </Box>
  );
}

export default ConfirmationStep;
