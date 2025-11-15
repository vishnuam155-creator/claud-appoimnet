# REST API Documentation

## Overview

This medical appointment booking system has been converted to a **pure REST API format**. All template-based views have been removed, leaving only clean, well-structured API endpoints.

## What Changed

### ✅ Removed
- All template rendering functions (`render()` calls)
- HTML template routes (home, chatbot page, voice assistant page, admin dashboard UI, etc.)
- Form-based views

### ✅ Added
- Django REST Framework serializers for all models
- Proper REST API views with consistent response format
- Comprehensive API documentation endpoint
- Pagination support for list endpoints
- Filter and search capabilities
- Health check endpoint

## Base URL

```
http://localhost:8000/
```

## Quick Start

### 1. API Documentation Endpoint

Get comprehensive API information:

```bash
GET /api/docs/
```

Returns complete API documentation in JSON format.

### 2. Health Check

```bash
GET /api/health/
```

Response:
```json
{
  "success": true,
  "status": "healthy",
  "message": "Medical Appointment Booking API is running"
}
```

## API Endpoints

### Patient Booking APIs

#### 1. Chatbot API

**Endpoint:** `POST /api/chatbot/`

**Description:** Process chatbot conversation messages

**Request:**
```json
{
  "message": "I need to book an appointment",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "abc-123",
  "message": "Sure! What symptoms are you experiencing?",
  "action": "ask_symptoms",
  "options": [],
  "booking_id": null
}
```

#### 2. Voice API

**Endpoint:** `POST /api/voice/`

**Description:** Transcribe audio or synthesize speech

**Transcribe Audio:**
```json
{
  "action": "transcribe",
  "audio_data": "base64-encoded-audio",
  "audio_format": "webm"
}
```

**Synthesize Speech:**
```json
{
  "action": "synthesize",
  "text": "Your appointment is confirmed",
  "language": "en-IN"
}
```

#### 3. Voice Assistant API

**Endpoint:** `POST /api/voice-assistant/`

**Description:** Voice-based conversation flow

**Request:**
```json
{
  "message": "I need a doctor for knee pain",
  "session_id": "optional-session-id",
  "session_data": {}
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "xyz-456",
  "message": "I can help with that. When would you like to schedule?",
  "stage": "date_selection",
  "action": "continue",
  "data": {}
}
```

---

### Admin Panel APIs

**Authentication Required:** All admin panel endpoints require staff/admin authentication

#### 1. Dashboard Statistics

**Endpoint:** `GET /admin-panel/api/dashboard/`

**Description:** Get dashboard statistics and overview

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_appointments": 150,
    "today_appointments": 10,
    "pending_appointments": 25,
    "confirmed_appointments": 100
  },
  "upcoming_appointments": [...],
  "recent_appointments": [...],
  "status_breakdown": [...]
}
```

#### 2. List Appointments

**Endpoint:** `GET /admin-panel/api/appointments/`

**Description:** List all appointments with filters and pagination

**Query Parameters:**
- `status` - Filter by status (pending, confirmed, cancelled, completed, no_show)
- `doctor` - Filter by doctor ID
- `date` - Filter by date (YYYY-MM-DD)
- `search` - Search by patient name, phone, or booking ID
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20)

**Example:**
```bash
GET /admin-panel/api/appointments/?status=pending&page=1&page_size=20
```

**Response:**
```json
{
  "success": true,
  "count": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "appointments": [
    {
      "id": 1,
      "booking_id": "APT12345678",
      "patient_name": "John Doe",
      "patient_phone": "+919876543210",
      "doctor": {
        "id": 1,
        "name": "Dr. Smith",
        "specialization": {
          "id": 1,
          "name": "Orthopedics"
        }
      },
      "appointment_date": "2025-11-20",
      "appointment_time": "10:00:00",
      "status": "pending",
      "created_at": "2025-11-14T10:00:00Z"
    }
  ]
}
```

#### 3. Get Appointment Details

**Endpoint:** `GET /admin-panel/api/appointments/{booking_id}/`

**Description:** Get detailed appointment information including history and SMS notifications

**Example:**
```bash
GET /admin-panel/api/appointments/APT12345678/
```

**Response:**
```json
{
  "success": true,
  "appointment": {
    "id": 1,
    "booking_id": "APT12345678",
    "patient_name": "John Doe",
    "doctor": {...},
    "history": [
      {
        "action": "creation",
        "status": "pending",
        "changed_by": "chatbot",
        "changed_at": "2025-11-14T10:00:00Z"
      }
    ],
    "sms_notifications": [...]
  }
}
```

#### 4. Update Appointment Status

**Endpoint:** `PUT /admin-panel/api/appointments/{booking_id}/update/`

**Description:** Update appointment status

**Request:**
```json
{
  "status": "confirmed",
  "notes": "Confirmed by admin",
  "changed_by": "admin_user"
}
```

**Status Options:**
- `pending`
- `confirmed`
- `cancelled`
- `completed`
- `no_show`

**Response:**
```json
{
  "success": true,
  "message": "Appointment status updated to confirmed",
  "appointment": {...}
}
```

#### 5. Calendar Data

**Endpoint:** `GET /admin-panel/api/calendar/`

**Description:** Get calendar data for a specific month

**Query Parameters:**
- `year` - Year (default: current year)
- `month` - Month 1-12 (default: current month)

**Example:**
```bash
GET /admin-panel/api/calendar/?year=2025&month=11
```

**Response:**
```json
{
  "success": true,
  "year": 2025,
  "month": 11,
  "month_name": "November",
  "calendar_weeks": [...],
  "appointments_by_date": {
    "2025-11-14": {
      "count": 5,
      "appointments": [...]
    }
  },
  "today": "2025-11-14",
  "navigation": {
    "prev_month": 10,
    "prev_year": 2025,
    "next_month": 12,
    "next_year": 2025
  }
}
```

#### 6. Appointments by Date

**Endpoint:** `GET /admin-panel/api/appointments-by-date/`

**Description:** Get all appointments for a specific date

**Query Parameters:**
- `date` - Date in YYYY-MM-DD format (required)

**Example:**
```bash
GET /admin-panel/api/appointments-by-date/?date=2025-11-20
```

**Response:**
```json
{
  "success": true,
  "date": "2025-11-20",
  "count": 8,
  "appointments": [...]
}
```

---

### WhatsApp Integration APIs

#### 1. WhatsApp Webhook (Meta)

**Endpoint:** `GET/POST /whatsapp/webhook/`

**Description:**
- GET: Webhook verification for Meta
- POST: Receive incoming WhatsApp messages

**Used by:** Meta WhatsApp Cloud API

#### 2. WhatsApp Status Webhook

**Endpoint:** `POST /whatsapp/webhook/status/`

**Description:** Receive message status updates from Meta

#### 3. Get WhatsApp Sessions

**Endpoint:** `GET /whatsapp/api/sessions/`

**Description:** Get all WhatsApp conversation sessions

**Query Parameters:**
- `is_active` - Filter by active status (true/false)
- `phone_number` - Filter by phone number
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 50)

**Example:**
```bash
GET /whatsapp/api/sessions/?is_active=true&page=1
```

**Response:**
```json
{
  "success": true,
  "count": 25,
  "page": 1,
  "page_size": 50,
  "total_pages": 1,
  "sessions": [
    {
      "id": 1,
      "session_id": "abc-123",
      "phone_number": "+919876543210",
      "is_active": true,
      "last_message_at": "2025-11-14T10:00:00Z",
      "appointment_booking_id": "APT12345678"
    }
  ]
}
```

#### 4. Get Session Messages

**Endpoint:** `GET /whatsapp/api/sessions/{session_id}/messages/`

**Description:** Get all messages for a specific session

**Example:**
```bash
GET /whatsapp/api/sessions/abc-123/messages/
```

**Response:**
```json
{
  "success": true,
  "session_id": "abc-123",
  "count": 10,
  "messages": [
    {
      "id": 1,
      "from_number": "+919876543210",
      "to_number": "+911234567890",
      "body": "I need an appointment",
      "direction": "inbound",
      "timestamp": "2025-11-14T10:00:00Z",
      "status": "delivered"
    }
  ]
}
```

---

### Voicebot APIs

The voicebot module retains its existing REST API structure:

- `POST /voicebot/api/intelligence/` - Main voice intelligence endpoint
- `POST /voicebot/api/database-action/` - Execute database actions
- `POST /voicebot/api/intent-analysis/` - Analyze intent only
- `GET/DELETE /voicebot/api/session/` - Session management

Refer to voicebot documentation for detailed usage.

---

## Data Models

### Appointment

```json
{
  "id": 1,
  "booking_id": "APT12345678",
  "doctor": {...},
  "patient_name": "John Doe",
  "patient_phone": "+919876543210",
  "patient_email": "john@example.com",
  "patient_age": 30,
  "patient_gender": "male",
  "appointment_date": "2025-11-20",
  "appointment_time": "10:00:00",
  "symptoms": "Knee pain",
  "notes": "Additional notes",
  "status": "pending",
  "session_id": "abc-123",
  "created_at": "2025-11-14T10:00:00Z",
  "updated_at": "2025-11-14T10:00:00Z"
}
```

**Status Options:**
- `pending` - Awaiting confirmation
- `confirmed` - Confirmed appointment
- `cancelled` - Cancelled by patient or admin
- `completed` - Appointment completed
- `no_show` - Patient didn't show up

### Doctor

```json
{
  "id": 1,
  "name": "Dr. Smith",
  "specialization": {
    "id": 1,
    "name": "Orthopedics",
    "description": "Bone and joint specialist"
  },
  "phone": "+919876543210",
  "email": "dr.smith@example.com",
  "qualification": "MBBS, MD",
  "experience_years": 10,
  "consultation_fee": "500.00",
  "is_active": true,
  "photo": "/media/doctors/smith.jpg",
  "bio": "Experienced orthopedic surgeon"
}
```

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": "...",
  "message": "Optional success message"
}
```

### Error Response

```json
{
  "success": false,
  "error": "Error message",
  "details": "Optional error details"
}
```

---

## Authentication

- **Public Endpoints:** Chatbot, Voice, WhatsApp webhooks (no authentication required)
- **Admin Endpoints:** Require Django staff/admin authentication
- **CSRF:** All API endpoints are CSRF exempt for easy integration

---

## File Structure

### New Files Created

```
appointments/
  ├── serializers.py          # NEW: DRF serializers for Appointment models

doctors/
  ├── serializers.py          # NEW: DRF serializers for Doctor models

whatsapp_integration/
  ├── serializers.py          # NEW: DRF serializers for WhatsApp models

admin_panel/
  ├── api_views.py            # NEW: REST API views for admin panel

config/
  ├── api_docs_views.py       # NEW: API documentation endpoint
```

### Modified Files

```
patient_booking/
  ├── views.py                # MODIFIED: Removed template views, kept only API views
  ├── urls.py                 # MODIFIED: Removed template routes

admin_panel/
  ├── urls.py                 # MODIFIED: Updated to use new API views

whatsapp_integration/
  ├── views.py                # MODIFIED: Removed template views, added session API
  ├── urls.py                 # MODIFIED: Removed template routes

config/
  ├── urls.py                 # MODIFIED: Added API documentation endpoints
```

---

## Testing the APIs

### Using cURL

#### Get API Documentation
```bash
curl http://localhost:8000/api/docs/
```

#### Health Check
```bash
curl http://localhost:8000/api/health/
```

#### Send Chatbot Message
```bash
curl -X POST http://localhost:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to book an appointment",
    "session_id": "test-123"
  }'
```

#### List Appointments (requires admin auth)
```bash
curl -X GET "http://localhost:8000/admin-panel/api/appointments/?page=1&page_size=10" \
  -H "Authorization: Token YOUR_AUTH_TOKEN"
```

### Using Postman

1. Import the API documentation from `/api/docs/`
2. Set base URL to `http://localhost:8000`
3. For admin endpoints, add authentication headers
4. Test each endpoint with sample data

### Using Python Requests

```python
import requests

# Health check
response = requests.get('http://localhost:8000/api/health/')
print(response.json())

# Chatbot message
response = requests.post('http://localhost:8000/api/chatbot/', json={
    'message': 'I need an appointment',
    'session_id': 'test-session'
})
print(response.json())

# List appointments (with auth)
headers = {'Authorization': 'Token YOUR_TOKEN'}
response = requests.get(
    'http://localhost:8000/admin-panel/api/appointments/',
    headers=headers
)
print(response.json())
```

---

## Migration Guide

### For Frontend Developers

1. **Remove all HTML templates** - This is now a pure API backend
2. **Build a separate frontend** using React, Vue, Angular, or any framework
3. **Use the API endpoints** documented above
4. **Handle authentication** for admin features
5. **Implement proper error handling** for API responses

### For Mobile App Developers

1. Use the REST API endpoints directly
2. No need for web scraping or HTML parsing
3. Clean JSON responses for easy data parsing
4. Pagination support for large datasets

### For Integration Partners

1. Use the `/api/docs/` endpoint to discover all APIs
2. Webhook support for WhatsApp integration
3. Real-time appointment management via API
4. Export/import capabilities through API endpoints

---

## Next Steps

1. **Add Authentication Tokens:** Implement JWT or Token-based auth for admin APIs
2. **API Rate Limiting:** Add rate limiting to prevent abuse
3. **API Versioning:** Consider adding `/api/v1/`, `/api/v2/` versioning
4. **OpenAPI/Swagger:** Generate OpenAPI specification for better tooling
5. **Build Frontend:** Create a modern frontend (React/Vue) to consume these APIs

---

## Support

For questions or issues, refer to:
- API Documentation: `GET /api/docs/`
- Main README: See `README.md`
- Codebase Exploration: See `CODEBASE_EXPLORATION.md`

---

## Summary

🎉 **Conversion Complete!**

- ✅ All template views removed
- ✅ Clean REST API structure
- ✅ Comprehensive serializers
- ✅ Proper error handling
- ✅ Pagination and filtering
- ✅ API documentation endpoint
- ✅ Consistent response format

This is now a **production-ready REST API** that can be consumed by any frontend framework, mobile app, or third-party integration!
