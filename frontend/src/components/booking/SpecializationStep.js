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
} from '@mui/material';
import { ArrowBack, ArrowForward, CheckCircle } from '@mui/icons-material';
import { getSpecializations } from '../../services/doctorService';

function SpecializationStep({ symptoms, selectedSpecialization, onSelect, onNext, onBack }) {
  const { data: specializations, isLoading, error } = useQuery({
    queryKey: ['specializations'],
    queryFn: getSpecializations,
  });

  const handleNext = () => {
    if (selectedSpecialization) {
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
        Failed to load specializations. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select Medical Specialization
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Based on your symptoms: <strong>{symptoms}</strong>
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {specializations?.results?.map((spec) => (
          <Grid item xs={12} sm={6} key={spec.id}>
            <Card
              sx={{
                border: selectedSpecialization?.id === spec.id ? '2px solid' : '1px solid',
                borderColor: selectedSpecialization?.id === spec.id ? 'primary.main' : 'divider',
              }}
            >
              <CardActionArea onClick={() => onSelect(spec)}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6">{spec.name}</Typography>
                    {selectedSpecialization?.id === spec.id && (
                      <CheckCircle color="primary" />
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {spec.description}
                  </Typography>
                  <Chip
                    label={`${spec.doctors_count} doctors`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
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
          disabled={!selectedSpecialization}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}

export default SpecializationStep;
