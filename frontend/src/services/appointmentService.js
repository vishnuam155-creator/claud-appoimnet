import apiClient from './api';

/**
 * Appointment Service - API calls for appointment-related operations
 */

// Appointments
export const getAppointments = async (params = {}) => {
  const response = await apiClient.get('/appointments/', { params });
  return response.data;
};

export const getAppointment = async (bookingId) => {
  const response = await apiClient.get(`/appointments/${bookingId}/`);
  return response.data;
};

export const createAppointment = async (appointmentData) => {
  const response = await apiClient.post('/appointments/', appointmentData);
  return response.data;
};

export const updateAppointment = async (bookingId, appointmentData) => {
  const response = await apiClient.put(`/appointments/${bookingId}/`, appointmentData);
  return response.data;
};

export const deleteAppointment = async (bookingId) => {
  const response = await apiClient.delete(`/appointments/${bookingId}/`);
  return response.data;
};

// Appointment Status
export const updateAppointmentStatus = async (bookingId, statusData) => {
  const response = await apiClient.patch(
    `/appointments/${bookingId}/update_status/`,
    statusData
  );
  return response.data;
};

export const cancelAppointment = async (bookingId, reason, changedBy = 'patient') => {
  const response = await apiClient.patch(
    `/appointments/${bookingId}/update_status/`,
    {
      status: 'cancelled',
      reason,
      changed_by: changedBy
    }
  );
  return response.data;
};

// Appointment Reschedule
export const rescheduleAppointment = async (bookingId, rescheduleData) => {
  const response = await apiClient.post(
    `/appointments/${bookingId}/reschedule/`,
    rescheduleData
  );
  return response.data;
};

// Appointment History
export const getAppointmentHistory = async (bookingId) => {
  const response = await apiClient.get(`/appointments/${bookingId}/history/`);
  return response.data;
};

// Appointment Notifications
export const getAppointmentNotifications = async (bookingId) => {
  const response = await apiClient.get(`/appointments/${bookingId}/notifications/`);
  return response.data;
};

// Patient Search
export const searchPatientAppointments = async (searchData) => {
  const response = await apiClient.post('/appointments/search_patient/', searchData);
  return response.data;
};

// Appointment Statistics
export const getAppointmentStatistics = async () => {
  const response = await apiClient.get('/appointments/statistics/');
  return response.data;
};

// SMS Notifications
export const resendSMSNotification = async (appointmentId, notificationType) => {
  const response = await apiClient.post('/sms-notifications/resend/', {
    appointment_id: appointmentId,
    notification_type: notificationType
  });
  return response.data;
};
