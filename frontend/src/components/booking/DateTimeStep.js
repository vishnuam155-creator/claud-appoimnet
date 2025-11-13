import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Button,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { ArrowBack, ArrowForward, CheckCircle } from '@mui/icons-material';
import { format, addDays } from 'date-fns';
import { getDoctorAvailability } from '../../services/doctorService';

function DateTimeStep({ doctor, selectedDate, selectedTime, onSelect, onNext, onBack }) {
  const [currentDate, setCurrentDate] = useState(selectedDate || format(new Date(), 'yyyy-MM-dd'));

  // Generate next 7 days
  const dates = Array.from({ length: 7 }, (_, i) => {
    const date = addDays(new Date(), i);
    return format(date, 'yyyy-MM-dd');
  });

  const { data: availability, isLoading, error } = useQuery({
    queryKey: ['availability', doctor?.id, currentDate],
    queryFn: () => getDoctorAvailability(doctor.id, currentDate, 1),
    enabled: !!doctor?.id && !!currentDate,
  });

  const handleDateSelect = (date) => {
    setCurrentDate(date);
    onSelect(date, null); // Reset time when date changes
  };

  const handleTimeSelect = (time) => {
    onSelect(currentDate, time);
  };

  const handleNext = () => {
    if (selectedDate && selectedTime) {
      onNext();
    }
  };

  // Get available slots for the current date
  const availableSlots = availability?.slots?.filter(slot =>
    slot.date === currentDate && slot.is_available
  ) || [];

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
        Failed to load availability. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Select Date and Time
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Choose your preferred appointment slot with Dr. {doctor?.name}
      </Typography>

      {/* Date Selection */}
      <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
        Select Date
      </Typography>
      <Grid container spacing={1} sx={{ mb: 4 }}>
        {dates.map((date) => {
          const dateObj = new Date(date);
          const isSelected = currentDate === date;
          return (
            <Grid item xs={12} sm={6} md={3} key={date}>
              <Chip
                label={`${format(dateObj, 'EEE, MMM d')}`}
                onClick={() => handleDateSelect(date)}
                color={isSelected ? 'primary' : 'default'}
                variant={isSelected ? 'filled' : 'outlined'}
                icon={isSelected ? <CheckCircle /> : undefined}
                sx={{ width: '100%', justifyContent: 'flex-start', py: 2 }}
              />
            </Grid>
          );
        })}
      </Grid>

      {/* Time Selection */}
      {currentDate && (
        <>
          <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600 }}>
            Select Time
          </Typography>
          {availableSlots.length > 0 ? (
            <Grid container spacing={1} sx={{ mb: 3 }}>
              {availableSlots.map((slot) => {
                const isSelected = selectedTime === slot.time;
                return (
                  <Grid item xs={6} sm={4} md={3} key={slot.time}>
                    <Chip
                      label={slot.time}
                      onClick={() => handleTimeSelect(slot.time)}
                      color={isSelected ? 'primary' : 'default'}
                      variant={isSelected ? 'filled' : 'outlined'}
                      icon={isSelected ? <CheckCircle /> : undefined}
                      sx={{ width: '100%', py: 2 }}
                    />
                  </Grid>
                );
              })}
            </Grid>
          ) : (
            <Alert severity="info" sx={{ mb: 3 }}>
              No available slots for this date. Please select another date.
            </Alert>
          )}
        </>
      )}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
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
          disabled={!selectedDate || !selectedTime}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}

export default DateTimeStep;
