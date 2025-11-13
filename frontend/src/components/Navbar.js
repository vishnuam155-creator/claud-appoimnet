import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from '@mui/material';
import {
  LocalHospital,
  CalendarMonth,
  People,
  Dashboard,
} from '@mui/icons-material';

function Navbar() {
  return (
    <AppBar position="static">
      <Container maxWidth="lg">
        <Toolbar disableGutters>
          <LocalHospital sx={{ mr: 1 }} />
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              flexGrow: 1,
              textDecoration: 'none',
              color: 'inherit',
              fontWeight: 700,
            }}
          >
            Medical Appointment System
          </Typography>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              color="inherit"
              component={RouterLink}
              to="/book"
              startIcon={<CalendarMonth />}
            >
              Book Appointment
            </Button>
            <Button
              color="inherit"
              component={RouterLink}
              to="/doctors"
              startIcon={<People />}
            >
              Doctors
            </Button>
            <Button
              color="inherit"
              component={RouterLink}
              to="/my-appointments"
            >
              My Appointments
            </Button>
            <Button
              color="inherit"
              component={RouterLink}
              to="/admin"
              startIcon={<Dashboard />}
            >
              Admin
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Navbar;
