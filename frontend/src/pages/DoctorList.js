import React, { useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Avatar,
  Chip,
} from '@mui/material';
import { Search, Star } from '@mui/icons-material';
import { getDoctors, getSpecializations } from '../services/doctorService';

function DoctorList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [specializationFilter, setSpecializationFilter] = useState('');

  const { data: doctors, isLoading, error } = useQuery({
    queryKey: ['doctors', specializationFilter],
    queryFn: () => getDoctors(
      specializationFilter ? { specialization: specializationFilter } : {}
    ),
  });

  const { data: specializations } = useQuery({
    queryKey: ['specializations'],
    queryFn: getSpecializations,
  });

  const filteredDoctors = doctors?.results?.filter((doctor) =>
    doctor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    doctor.qualification.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" gutterBottom>
        Our Doctors
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Find the right doctor for your medical needs
      </Typography>

      {/* Filters */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by name or qualification..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              label="Filter by Specialization"
              value={specializationFilter}
              onChange={(e) => setSpecializationFilter(e.target.value)}
            >
              <MenuItem value="">All Specializations</MenuItem>
              {specializations?.results?.map((spec) => (
                <MenuItem key={spec.id} value={spec.id}>
                  {spec.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </Box>

      {/* Doctor List */}
      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">Failed to load doctors. Please try again.</Alert>
      ) : (
        <Grid container spacing={3}>
          {filteredDoctors?.map((doctor) => (
            <Grid item xs={12} sm={6} md={4} key={doctor.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
                    <Avatar
                      src={doctor.photo_url}
                      alt={doctor.name}
                      sx={{ width: 80, height: 80, mb: 1 }}
                    />
                    <Typography variant="h6" align="center">
                      Dr. {doctor.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" align="center">
                      {doctor.specialization_name}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {doctor.qualification}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 2 }}>
                    <Chip
                      icon={<Star />}
                      label={`${doctor.experience_years} years`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip
                      label={`₹${doctor.consultation_fee}`}
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    fullWidth
                    variant="contained"
                    component={RouterLink}
                    to={`/doctors/${doctor.id}`}
                  >
                    View Profile & Book
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {filteredDoctors?.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6" color="text.secondary">
            No doctors found matching your criteria
          </Typography>
        </Box>
      )}
    </Container>
  );
}

export default DoctorList;
