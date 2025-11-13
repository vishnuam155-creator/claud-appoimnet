import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Container,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Paper,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  getSpecializations,
  getDoctors,
  getDoctorAvailability,
} from '../services/doctorService';
import { createAppointment } from '../services/appointmentService';

// Step Components
import SymptomStep from '../components/booking/SymptomStep';
import SpecializationStep from '../components/booking/SpecializationStep';
import DoctorStep from '../components/booking/DoctorStep';
import DateTimeStep from '../components/booking/DateTimeStep';
import PatientDetailsStep from '../components/booking/PatientDetailsStep';
import ConfirmationStep from '../components/booking/ConfirmationStep';

const steps = [
  'Symptoms',
  'Specialization',
  'Select Doctor',
  'Date & Time',
  'Your Details',
  'Confirm',
];

function BookAppointment() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [bookingData, setBookingData] = useState({
    symptoms: '',
    specialization: null,
    doctor: null,
    date: null,
    time: null,
    patientName: '',
    patientPhone: '',
    patientEmail: '',
    patientAge: '',
    patientGender: '',
    notes: '',
  });
  const [error, setError] = useState(null);

  // Create appointment mutation
  const createAppointmentMutation = useMutation({
    mutationFn: createAppointment,
    onSuccess: (data) => {
      navigate(`/confirmation/${data.booking_id}`);
    },
    onError: (error) => {
      setError(error.response?.data?.detail || 'Failed to create appointment');
    },
  });

  const handleNext = () => {
    setError(null);
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleUpdateBookingData = (data) => {
    setBookingData((prev) => ({ ...prev, ...data }));
  };

  const handleSubmit = async () => {
    const appointmentData = {
      doctor: bookingData.doctor.id,
      patient_name: bookingData.patientName,
      patient_phone: bookingData.patientPhone,
      patient_email: bookingData.patientEmail,
      patient_age: bookingData.patientAge ? parseInt(bookingData.patientAge) : null,
      patient_gender: bookingData.patientGender,
      appointment_date: bookingData.date,
      appointment_time: bookingData.time,
      symptoms: bookingData.symptoms,
      notes: bookingData.notes,
    };

    createAppointmentMutation.mutate(appointmentData);
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <SymptomStep
            value={bookingData.symptoms}
            onChange={(symptoms) => handleUpdateBookingData({ symptoms })}
            onNext={handleNext}
          />
        );
      case 1:
        return (
          <SpecializationStep
            symptoms={bookingData.symptoms}
            selectedSpecialization={bookingData.specialization}
            onSelect={(specialization) =>
              handleUpdateBookingData({ specialization })
            }
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 2:
        return (
          <DoctorStep
            specializationId={bookingData.specialization?.id}
            selectedDoctor={bookingData.doctor}
            onSelect={(doctor) => handleUpdateBookingData({ doctor })}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 3:
        return (
          <DateTimeStep
            doctor={bookingData.doctor}
            selectedDate={bookingData.date}
            selectedTime={bookingData.time}
            onSelect={(date, time) => handleUpdateBookingData({ date, time })}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 4:
        return (
          <PatientDetailsStep
            data={bookingData}
            onChange={handleUpdateBookingData}
            onNext={handleNext}
            onBack={handleBack}
          />
        );
      case 5:
        return (
          <ConfirmationStep
            data={bookingData}
            onBack={handleBack}
            onSubmit={handleSubmit}
            isLoading={createAppointmentMutation.isPending}
          />
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom align="center">
          Book an Appointment
        </Typography>

        <Stepper activeStep={activeStep} sx={{ my: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 4 }}>{getStepContent(activeStep)}</Box>
      </Paper>
    </Container>
  );
}

export default BookAppointment;
