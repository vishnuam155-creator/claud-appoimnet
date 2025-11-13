# REST API Documentation

## Overview

This document provides comprehensive documentation for the Medical Appointment System REST API built with Django REST Framework.

**Base URL:** `http://localhost:8000/api/v1/`

## API Endpoints

### Specializations

#### List all specializations
```http
GET /api/v1/specializations/
```

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Cardiology",
      "description": "Heart and cardiovascular system",
      "keywords": "heart, cardiac, chest pain",
      "keywords_list": ["heart", "cardiac", "chest pain"],
      "doctors_count": 5,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Get specialization doctors
```http
GET /api/v1/specializations/{id}/doctors/
```

### Doctors

#### List all doctors
```http
GET /api/v1/doctors/
```

**Query Parameters:**
- `specialization` - Filter by specialization ID
- `is_active` - Filter by active status (true/false)
- `search` - Search by name, qualification, or bio
- `ordering` - Order by field (name, experience_years, consultation_fee, created_at)
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)

**Response:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/doctors/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "specialization": 1,
      "specialization_name": "Cardiology",
      "phone": "+1234567890",
      "email": "john@example.com",
      "qualification": "MBBS, MD (Cardiology)",
      "experience_years": 15,
      "consultation_fee": "500.00",
      "is_active": true,
      "photo_url": "http://localhost:8000/media/doctors/john.jpg",
      "appointments_count": 10
    }
  ]
}
```

#### Get doctor details
```http
GET /api/v1/doctors/{id}/
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "specialization": 1,
  "specialization_name": "Cardiology",
  "specialization_detail": {
    "id": 1,
    "name": "Cardiology",
    "description": "Heart and cardiovascular system"
  },
  "phone": "+1234567890",
  "email": "john@example.com",
  "qualification": "MBBS, MD (Cardiology)",
  "experience_years": 15,
  "consultation_fee": "500.00",
  "is_active": true,
  "photo": "/media/doctors/john.jpg",
  "photo_url": "http://localhost:8000/media/doctors/john.jpg",
  "bio": "Experienced cardiologist with 15 years of practice...",
  "schedules": [
    {
      "id": 1,
      "doctor": 1,
      "day_of_week": 0,
      "day_name": "Monday",
      "start_time": "09:00:00",
      "end_time": "17:00:00",
      "slot_duration": 30,
      "is_active": true
    }
  ],
  "leaves": [],
  "upcoming_leaves": [],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### Create doctor
```http
POST /api/v1/doctors/
```

**Request Body:**
```json
{
  "name": "Jane Smith",
  "specialization": 1,
  "phone": "+1234567890",
  "email": "jane@example.com",
  "qualification": "MBBS, MD",
  "experience_years": 10,
  "consultation_fee": "400.00",
  "is_active": true,
  "bio": "Dedicated cardiologist..."
}
```

#### Update doctor
```http
PUT /api/v1/doctors/{id}/
PATCH /api/v1/doctors/{id}/
```

#### Delete doctor
```http
DELETE /api/v1/doctors/{id}/
```

#### Search doctors
```http
GET /api/v1/doctors/search/?q=cardiology
```

#### Get doctor availability
```http
GET /api/v1/doctors/{id}/availability/?date=2025-01-15&days=7
```

**Query Parameters:**
- `date` (required) - Start date in YYYY-MM-DD format
- `days` (optional) - Number of days to fetch (default: 1)

**Response:**
```json
{
  "doctor": {
    "id": 1,
    "name": "John Doe",
    "specialization_name": "Cardiology"
  },
  "date_range": {
    "start": "2025-01-15",
    "end": "2025-01-21"
  },
  "slots": [
    {
      "date": "2025-01-15",
      "time": "09:00:00",
      "doctor": 1,
      "doctor_name": "John Doe",
      "is_available": true,
      "reason": ""
    },
    {
      "date": "2025-01-15",
      "time": "09:30:00",
      "doctor": 1,
      "doctor_name": "John Doe",
      "is_available": false,
      "reason": "Already booked"
    }
  ]
}
```

### Appointments

#### List all appointments
```http
GET /api/v1/appointments/
```

**Query Parameters:**
- `doctor` - Filter by doctor ID
- `status` - Filter by status (pending, confirmed, cancelled, completed, no_show)
- `appointment_date` - Filter by date (YYYY-MM-DD)
- `start_date` - Filter appointments from this date
- `end_date` - Filter appointments until this date
- `phone` - Filter by patient phone
- `upcoming` - Show only upcoming appointments (true/false)
- `search` - Search by patient name, phone, email, or booking ID
- `ordering` - Order by field
- `page` - Page number
- `page_size` - Items per page

**Response:**
```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "booking_id": "APT12345ABC",
      "doctor": 1,
      "doctor_name": "John Doe",
      "specialization_name": "Cardiology",
      "patient_name": "Alice Johnson",
      "patient_phone": "+1234567890",
      "appointment_date": "2025-01-15",
      "appointment_time": "10:00:00",
      "status": "confirmed",
      "status_display": "Confirmed",
      "symptoms": "Chest pain and shortness of breath",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

#### Get appointment details
```http
GET /api/v1/appointments/{booking_id}/
```

**Response:**
```json
{
  "id": 1,
  "booking_id": "APT12345ABC",
  "doctor": 1,
  "doctor_detail": {
    "id": 1,
    "name": "John Doe",
    "specialization_name": "Cardiology",
    "phone": "+1234567890",
    "email": "john@example.com",
    "consultation_fee": "500.00"
  },
  "patient_name": "Alice Johnson",
  "patient_phone": "+1234567890",
  "patient_email": "alice@example.com",
  "patient_age": 35,
  "patient_gender": "female",
  "gender_display": "Female",
  "appointment_date": "2025-01-15",
  "appointment_time": "10:00:00",
  "symptoms": "Chest pain and shortness of breath",
  "notes": "Patient has history of heart issues",
  "status": "confirmed",
  "status_display": "Confirmed",
  "session_id": "abc123",
  "history": [
    {
      "id": 1,
      "status": "confirmed",
      "action": "creation",
      "changed_by": "patient",
      "changed_at": "2025-01-01T00:00:00Z",
      "notes": "Appointment created"
    }
  ],
  "sms_notifications": [],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### Create appointment
```http
POST /api/v1/appointments/
```

**Request Body:**
```json
{
  "doctor": 1,
  "patient_name": "Alice Johnson",
  "patient_phone": "+1234567890",
  "patient_email": "alice@example.com",
  "patient_age": 35,
  "patient_gender": "female",
  "appointment_date": "2025-01-15",
  "appointment_time": "10:00:00",
  "symptoms": "Chest pain and shortness of breath",
  "notes": "Patient has history of heart issues"
}
```

**Validation:**
- Checks if appointment date is not in the past
- Validates doctor's schedule for the selected day
- Checks if time falls within doctor's working hours
- Verifies doctor is not on leave
- Ensures slot is not already booked

**Success Response (201 Created):**
Returns detailed appointment object with booking ID and sends SMS confirmation.

#### Update appointment status
```http
PATCH /api/v1/appointments/{booking_id}/update_status/
```

**Request Body:**
```json
{
  "status": "confirmed",
  "reason": "Confirmed by receptionist",
  "changed_by": "admin"
}
```

**Valid Status Transitions:**
- `pending` → `confirmed`, `cancelled`
- `confirmed` → `completed`, `cancelled`, `no_show`
- `cancelled`, `completed`, `no_show` → No further changes allowed

#### Reschedule appointment
```http
POST /api/v1/appointments/{booking_id}/reschedule/
```

**Request Body:**
```json
{
  "new_date": "2025-01-20",
  "new_time": "14:00:00",
  "reason": "Patient requested reschedule",
  "changed_by": "patient"
}
```

#### Cancel appointment
```http
PATCH /api/v1/appointments/{booking_id}/update_status/
```

**Request Body:**
```json
{
  "status": "cancelled",
  "reason": "Patient unable to attend",
  "changed_by": "patient"
}
```

#### Get appointment history
```http
GET /api/v1/appointments/{booking_id}/history/
```

#### Search patient appointments
```http
POST /api/v1/appointments/search_patient/
```

**Request Body:**
```json
{
  "phone": "+1234567890"
}
```

or

```json
{
  "email": "alice@example.com"
}
```

**Response:**
```json
{
  "patient_phone": "+1234567890",
  "patient_email": "alice@example.com",
  "upcoming": [
    { /* appointment objects */ }
  ],
  "past": [
    { /* appointment objects */ }
  ],
  "cancelled": [
    { /* appointment objects */ }
  ]
}
```

#### Get appointment statistics
```http
GET /api/v1/appointments/statistics/
```

**Response:**
```json
{
  "total": 150,
  "by_status": {
    "pending": 20,
    "confirmed": 50,
    "completed": 60,
    "cancelled": 15,
    "no_show": 5
  },
  "upcoming": 70,
  "today": 10
}
```

### SMS Notifications

#### List SMS notifications
```http
GET /api/v1/sms-notifications/
```

**Query Parameters:**
- `appointment` - Filter by appointment ID
- `notification_type` - Filter by type (confirmation, reminder, cancellation, reschedule)
- `status` - Filter by status (sent, delivered, failed, undelivered)

#### Resend SMS notification
```http
POST /api/v1/sms-notifications/resend/
```

**Request Body:**
```json
{
  "appointment_id": "APT12345ABC",
  "notification_type": "reminder"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Validation error
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "field_name": [
    "Error message"
  ]
}
```

or

```json
{
  "detail": "Error message"
}
```

## Pagination

All list endpoints support pagination:

**Request:**
```http
GET /api/v1/doctors/?page=2&page_size=10
```

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/doctors/?page=3",
  "previous": "http://localhost:8000/api/v1/doctors/?page=1",
  "results": []
}
```

## Authentication

Currently, all endpoints use `AllowAny` permission. For production, implement token-based authentication:

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

Then include the token in requests:
```http
Authorization: Token your_token_here
```
