import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActionArea,
  CircularProgress,
  Alert,
  Chip,
  Avatar,
} from '@mui/material';
import { ArrowBack, ArrowForward, CheckCircle, Star } from '@mui/icons-material';
import { getDoctors } from '../../services/doctorService';

function DoctorStep({ specializationId, selectedDoctor, onSelect, onNext, onBack }) {
  const { data: doctors, isLoading, error } = useQuery({
    queryKey: ['doctors', specializationId],
    queryFn: () => getDoctors({ specialization: specializationId }),
    enabled: !!specializationId,
  });

  const handleNext = () => {
    if (selectedDoctor) {
      onNext();
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load doctors. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select a Doctor
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose from our qualified doctors in this specialization
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {doctors?.results?.map((doctor) => (
          <Grid item xs={12} key={doctor.id}>
            <Card
              sx={{
                border: selectedDoctor?.id === doctor.id ? '2px solid' : '1px solid',
                borderColor: selectedDoctor?.id === doctor.id ? 'primary.main' : 'divider',
              }}
            >
              <CardActionArea onClick={() => onSelect(doctor)}>
                <CardContent>
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Avatar
                      src={doctor.photo_url}
                      alt={doctor.name}
                      sx={{ width: 80, height: 80 }}
                    />
                    <Box sx={{ flexGrow: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box>
                          <Typography variant="h6">Dr. {doctor.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {doctor.qualification}
                          </Typography>
                        </Box>
                        {selectedDoctor?.id === doctor.id && (
                          <CheckCircle color="primary" />
                        )}
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, mt: 1, flexWrap: 'wrap' }}>
                        <Chip
                          icon={<Star />}
                          label={`${doctor.experience_years} years exp`}
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
                        {doctor.appointments_count > 0 && (
                          <Chip
                            label={`${doctor.appointments_count} appointments`}
                            size="small"
                          />
                        )}
                      </Box>
                    </Box>
                  </Box>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
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
          disabled={!selectedDoctor}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}

export default DoctorStep;
