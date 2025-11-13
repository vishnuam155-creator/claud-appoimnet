import React from 'react';
import { useParams, Link as RouterLink } from 'react-router-dom';
import { useQuery } from '@tantml:invoke>
import {
  Container,
  Typography,
  Box,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Divider,
  Chip,
} from '@mui/material';
import { CheckCircle, Home, CalendarMonth } from '@mui/icons-material';
import { format } from 'date-fns';
import { getAppointment } from '../services/appointmentService';

function AppointmentConfirmation() {
  const { bookingId } = useParams();

  const { data: appointment, isLoading, error } = useQuery({
    queryKey: ['appointment', bookingId],
    queryFn: () => getAppointment(bookingId),
  });

  if (isLoading) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="sm" sx={{ py: 4 }}>
        <Alert severity="error">Failed to load appointment details.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
        <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />

        <Typography variant="h4" gutterBottom>
          Appointment Confirmed!
        </Typography>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Your appointment has been successfully booked
        </Typography>

        <Chip
          label={`Booking ID: ${appointment.booking_id}`}
          color="primary"
          sx={{ mb: 4 }}
        />

        <Divider sx={{ my: 3 }} />

        {/* Appointment Details */}
        <Box sx={{ textAlign: 'left', mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Doctor
            </Typography>
            <Typography variant="h6">
              Dr. {appointment.doctor_detail?.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {appointment.doctor_detail?.specialization_name}
            </Typography>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Date & Time
            </Typography>
            <Typography variant="body1">
              {format(new Date(appointment.appointment_date), 'EEEE, MMMM d, yyyy')}
            </Typography>
            <Typography variant="body1">
              {appointment.appointment_time}
            </Typography>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Patient
            </Typography>
            <Typography variant="body1">
              {appointment.patient_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {appointment.patient_phone}
            </Typography>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary">
              Status
            </Typography>
            <br />
            <Chip
              label={appointment.status_display}
              color={appointment.status === 'confirmed' ? 'success' : 'warning'}
              size="small"
            />
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Alert severity="info" sx={{ mb: 3, textAlign: 'left' }}>
          You will receive an SMS confirmation shortly. Please arrive 10 minutes before your scheduled time.
        </Alert>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="outlined"
            startIcon={<Home />}
            component={RouterLink}
            to="/"
          >
            Go Home
          </Button>
          <Button
            variant="contained"
            startIcon={<CalendarMonth />}
            component={RouterLink}
            to="/my-appointments"
          >
            My Appointments
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

export default AppointmentConfirmation;
