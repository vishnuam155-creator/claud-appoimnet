import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  People,
  CalendarMonth,
  CheckCircle,
  Cancel,
  HourglassEmpty,
} from '@mui/icons-material';
import { getAppointmentStatistics } from '../services/appointmentService';
import { getDoctors } from '../services/doctorService';

function AdminDashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['appointment-statistics'],
    queryFn: getAppointmentStatistics,
  });

  const { data: doctors, isLoading: doctorsLoading } = useQuery({
    queryKey: ['doctors'],
    queryFn: getDoctors,
  });

  const StatCard = ({ title, value, icon, color }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" color={color} gutterBottom>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
          <Box sx={{ color, opacity: 0.3 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (statsLoading || doctorsLoading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom>
        Admin Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Overview of your medical appointment system
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Appointments"
            value={stats?.total || 0}
            icon={<CalendarMonth sx={{ fontSize: 60 }} />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Today's Appointments"
            value={stats?.today || 0}
            icon={<HourglassEmpty sx={{ fontSize: 60 }} />}
            color="warning.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Upcoming"
            value={stats?.upcoming || 0}
            icon={<CheckCircle sx={{ fontSize: 60 }} />}
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Doctors"
            value={doctors?.count || doctors?.results?.length || 0}
            icon={<People sx={{ fontSize: 60 }} />}
            color="info.main"
          />
        </Grid>
      </Grid>

      {/* Status Breakdown */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Appointments by Status
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            {stats?.by_status && Object.entries(stats.by_status).map(([status, count]) => (
              <Grid item xs={6} sm={4} md={2.4} key={status}>
                <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="h4" color="primary">
                    {count}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                    {status.replace('_', ' ')}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Quick Info */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Information
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Backend API:</strong> Django REST Framework
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Frontend:</strong> React with Material-UI
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Features:</strong> Voice Bot, SMS Notifications, WhatsApp Integration
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Alert severity="info" sx={{ mt: 2 }}>
                Admin features like doctor management, appointment management, and analytics are coming soon!
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default AdminDashboard;
