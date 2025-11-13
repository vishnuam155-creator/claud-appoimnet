import apiClient from './api';

/**
 * Doctor Service - API calls for doctor-related operations
 */

// Specializations
export const getSpecializations = async () => {
  const response = await apiClient.get('/specializations/');
  return response.data;
};

export const getSpecialization = async (id) => {
  const response = await apiClient.get(`/specializations/${id}/`);
  return response.data;
};

export const getDoctorsBySpecialization = async (specializationId) => {
  const response = await apiClient.get(`/specializations/${specializationId}/doctors/`);
  return response.data;
};

// Doctors
export const getDoctors = async (params = {}) => {
  const response = await apiClient.get('/doctors/', { params });
  return response.data;
};

export const getDoctor = async (id) => {
  const response = await apiClient.get(`/doctors/${id}/`);
  return response.data;
};

export const createDoctor = async (doctorData) => {
  const response = await apiClient.post('/doctors/', doctorData);
  return response.data;
};

export const updateDoctor = async (id, doctorData) => {
  const response = await apiClient.put(`/doctors/${id}/`, doctorData);
  return response.data;
};

export const deleteDoctor = async (id) => {
  const response = await apiClient.delete(`/doctors/${id}/`);
  return response.data;
};

export const searchDoctors = async (searchTerm) => {
  const response = await apiClient.get('/doctors/search/', {
    params: { q: searchTerm }
  });
  return response.data;
};

// Doctor Availability
export const getDoctorAvailability = async (doctorId, date, days = 1) => {
  const response = await apiClient.get(`/doctors/${doctorId}/availability/`, {
    params: { date, days }
  });
  return response.data;
};

// Doctor Schedules
export const getDoctorSchedules = async (doctorId) => {
  const response = await apiClient.get(`/doctors/${doctorId}/schedules/`);
  return response.data;
};

export const addDoctorSchedule = async (doctorId, scheduleData) => {
  const response = await apiClient.post(`/doctors/${doctorId}/add_schedule/`, scheduleData);
  return response.data;
};

// Doctor Leaves
export const getDoctorLeaves = async (doctorId, upcomingOnly = false) => {
  const response = await apiClient.get(`/doctors/${doctorId}/leaves/`, {
    params: { upcoming: upcomingOnly }
  });
  return response.data;
};

export const addDoctorLeave = async (doctorId, leaveData) => {
  const response = await apiClient.post(`/doctors/${doctorId}/add_leave/`, leaveData);
  return response.data;
};
