import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Avatar,
  Chip,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import { CalendarMonth, Star, Phone, Email } from '@mui/icons-material';
import { getDoctor } from '../services/doctorService';

function DoctorDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: doctor, isLoading, error } = useQuery({
    queryKey: ['doctor', id],
    queryFn: () => getDoctor(id),
  });

  if (isLoading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">Failed to load doctor details. Please try again.</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Doctor Header */}
        <Box sx={{ display: 'flex', gap: 3, mb: 4 }}>
          <Avatar
            src={doctor.photo_url}
            alt={doctor.name}
            sx={{ width: 120, height: 120 }}
          />
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h4" gutterBottom>
              Dr. {doctor.name}
            </Typography>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {doctor.specialization_name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
              <Chip
                icon={<Star />}
                label={`${doctor.experience_years} years experience`}
                color="primary"
              />
              <Chip
                label={`₹${doctor.consultation_fee} consultation fee`}
                color="success"
              />
            </Box>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Qualification */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Qualification
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {doctor.qualification}
          </Typography>
        </Box>

        {/* Bio */}
        {doctor.bio && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              About
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {doctor.bio}
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 3 }} />

        {/* Contact Info */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Contact Information
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexDirection: 'column', mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Phone fontSize="small" />
              <Typography variant="body1">{doctor.phone}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Email fontSize="small" />
              <Typography variant="body1">{doctor.email}</Typography>
            </Box>
          </Box>
        </Box>

        {/* Schedule */}
        {doctor.schedules && doctor.schedules.length > 0 && (
          <>
            <Divider sx={{ my: 3 }} />
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Weekly Schedule
              </Typography>
              <Grid container spacing={1} sx={{ mt: 1 }}>
                {doctor.schedules.map((schedule) => (
                  <Grid item xs={12} sm={6} key={schedule.id}>
                    <Card variant="outlined">
                      <CardContent sx={{ py: 1.5 }}>
                        <Typography variant="body2" fontWeight={600}>
                          {schedule.day_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {schedule.start_time} - {schedule.end_time}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </>
        )}

        {/* Book Button */}
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<CalendarMonth />}
            onClick={() => navigate('/book')}
            sx={{ px: 6 }}
          >
            Book Appointment
          </Button>
        </Box>
      </Paper>
    </Container>
  );
}

export default DoctorDetail;
