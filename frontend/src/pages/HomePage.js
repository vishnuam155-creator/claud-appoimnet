import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Typography,
  Button,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import {
  CalendarMonth,
  People,
  LocalHospital,
  Phone,
} from '@mui/icons-material';

function HomePage() {
  const features = [
    {
      icon: <CalendarMonth sx={{ fontSize: 60, color: 'primary.main' }} />,
      title: 'Easy Booking',
      description: 'Book appointments with your preferred doctors in just a few clicks',
      action: 'Book Now',
      link: '/book',
    },
    {
      icon: <People sx={{ fontSize: 60, color: 'primary.main' }} />,
      title: 'Expert Doctors',
      description: 'Choose from our wide range of specialized medical professionals',
      action: 'View Doctors',
      link: '/doctors',
    },
    {
      icon: <LocalHospital sx={{ fontSize: 60, color: 'primary.main' }} />,
      title: 'Track Appointments',
      description: 'View and manage all your appointments in one place',
      action: 'My Appointments',
      link: '/my-appointments',
    },
    {
      icon: <Phone sx={{ fontSize: 60, color: 'primary.main' }} />,
      title: '24/7 Support',
      description: 'Get SMS notifications and reminders for your appointments',
      action: 'Learn More',
      link: '#',
    },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Box
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          py: 8,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h2" component="h1" gutterBottom>
            Welcome to Medical Appointment System
          </Typography>
          <Typography variant="h5" sx={{ mb: 4 }}>
            Book appointments with top doctors easily and conveniently
          </Typography>
          <Button
            variant="contained"
            size="large"
            color="secondary"
            component={RouterLink}
            to="/book"
            sx={{
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
            }}
          >
            Book an Appointment
          </Button>
        </Container>
      </Box>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ py: 8 }}>
        <Typography variant="h3" align="center" gutterBottom sx={{ mb: 6 }}>
          Why Choose Us?
        </Typography>
        <Grid container spacing={4}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  textAlign: 'center',
                  transition: 'transform 0.2s',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 4,
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1, pt: 4 }}>
                  <Box sx={{ mb: 2 }}>{feature.icon}</Box>
                  <Typography variant="h5" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                  <Button
                    size="medium"
                    component={RouterLink}
                    to={feature.link}
                    color="primary"
                  >
                    {feature.action}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box
        sx={{
          bgcolor: 'grey.100',
          py: 8,
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h4" gutterBottom>
            Ready to Get Started?
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Book your appointment today and experience quality healthcare
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              component={RouterLink}
              to="/book"
            >
              Book Appointment
            </Button>
            <Button
              variant="outlined"
              size="large"
              component={RouterLink}
              to="/doctors"
            >
              Browse Doctors
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  );
}

export default HomePage;
