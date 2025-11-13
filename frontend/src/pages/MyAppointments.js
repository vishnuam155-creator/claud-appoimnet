import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
} from '@mui/material';
import { Search, Cancel, Event } from '@mui/icons-material';
import { format } from 'date-fns';
import {
  searchPatientAppointments,
  cancelAppointment,
} from '../services/appointmentService';

function MyAppointments() {
  const queryClient = useQueryClient();
  const [phone, setPhone] = useState('');
  const [searchPerformed, setSearchPerformed] = useState(false);
  const [cancelDialog, setCancelDialog] = useState({ open: false, appointment: null });
  const [cancelReason, setCancelReason] = useState('');

  const { data: appointments, isLoading, error } = useQuery({
    queryKey: ['patient-appointments', phone],
    queryFn: () => searchPatientAppointments({ phone }),
    enabled: searchPerformed,
  });

  const cancelMutation = useMutation({
    mutationFn: ({ bookingId, reason }) => cancelAppointment(bookingId, reason, 'patient'),
    onSuccess: () => {
      queryClient.invalidateQueries(['patient-appointments']);
      setCancelDialog({ open: false, appointment: null });
      setCancelReason('');
    },
  });

  const handleSearch = () => {
    if (phone.trim()) {
      setSearchPerformed(true);
    }
  };

  const handleCancelClick = (appointment) => {
    setCancelDialog({ open: true, appointment });
  };

  const handleCancelConfirm = () => {
    if (cancelDialog.appointment) {
      cancelMutation.mutate({
        bookingId: cancelDialog.appointment.booking_id,
        reason: cancelReason,
      });
    }
  };

  const AppointmentCard = ({ appointment }) => {
    const isPast = new Date(appointment.appointment_date) < new Date();
    const canCancel = ['pending', 'confirmed'].includes(appointment.status) && !isPast;

    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                Dr. {appointment.doctor_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {appointment.specialization_name}
              </Typography>
            </Box>
            <Chip
              label={appointment.status_display}
              color={
                appointment.status === 'confirmed' ? 'success' :
                appointment.status === 'pending' ? 'warning' :
                appointment.status === 'cancelled' ? 'error' :
                'default'
              }
              size="small"
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Typography variant="caption" color="text.secondary">
                Date & Time
              </Typography>
              <Typography variant="body2">
                {format(new Date(appointment.appointment_date), 'MMM d, yyyy')} at {appointment.appointment_time}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="caption" color="text.secondary">
                Booking ID
              </Typography>
              <Typography variant="body2">
                {appointment.booking_id}
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="caption" color="text.secondary">
                Symptoms
              </Typography>
              <Typography variant="body2">
                {appointment.symptoms}
              </Typography>
            </Grid>
          </Grid>

          {canCancel && (
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                size="small"
                color="error"
                startIcon={<Cancel />}
                onClick={() => handleCancelClick(appointment)}
              >
                Cancel Appointment
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom>
        My Appointments
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        View and manage your appointments
      </Typography>

      {/* Search Box */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Find Your Appointments
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            label="Phone Number"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1234567890"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button
            variant="contained"
            startIcon={<Search />}
            onClick={handleSearch}
            disabled={!phone.trim()}
          >
            Search
          </Button>
        </Box>
      </Paper>

      {/* Results */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load appointments. Please try again.
        </Alert>
      )}

      {appointments && (
        <Box>
          {/* Upcoming Appointments */}
          {appointments.upcoming?.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Event /> Upcoming Appointments
              </Typography>
              {appointments.upcoming.map((apt) => (
                <AppointmentCard key={apt.id} appointment={apt} />
              ))}
            </Box>
          )}

          {/* Past Appointments */}
          {appointments.past?.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Past Appointments
              </Typography>
              {appointments.past.map((apt) => (
                <AppointmentCard key={apt.id} appointment={apt} />
              ))}
            </Box>
          )}

          {/* Cancelled Appointments */}
          {appointments.cancelled?.length > 0 && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Cancelled Appointments
              </Typography>
              {appointments.cancelled.map((apt) => (
                <AppointmentCard key={apt.id} appointment={apt} />
              ))}
            </Box>
          )}

          {/* No appointments */}
          {!appointments.upcoming?.length && !appointments.past?.length && !appointments.cancelled?.length && (
            <Alert severity="info">
              No appointments found for this phone number.
            </Alert>
          )}
        </Box>
      )}

      {/* Cancel Dialog */}
      <Dialog open={cancelDialog.open} onClose={() => setCancelDialog({ open: false, appointment: null })}>
        <DialogTitle>Cancel Appointment</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Are you sure you want to cancel this appointment?
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason for Cancellation (Optional)"
            value={cancelReason}
            onChange={(e) => setCancelReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog({ open: false, appointment: null })}>
            Keep Appointment
          </Button>
          <Button
            color="error"
            variant="contained"
            onClick={handleCancelConfirm}
            disabled={cancelMutation.isPending}
          >
            {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Appointment'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

export default MyAppointments;
