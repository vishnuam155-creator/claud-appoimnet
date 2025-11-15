# Frontend Integration Guide

## Problem

Your frontend at `http://localhost:8080` cannot connect to the backend because:

1. ✅ **CORS was blocking** - Fixed! Backend now allows requests from port 8080
2. ⚠️ **Backend might not be running** - You need to start Django server
3. ⚠️ **Old endpoints removed** - Template routes no longer exist

---

## Solution

### Step 1: Start the Backend Server

The Django backend must be running for your frontend to connect.

**Option A: Using Python directly**
```bash
cd /home/user/claud-appoimnet
python manage.py runserver 8000
```

**Option B: Using the start script**
```bash
cd /home/user/claud-appoimnet
./start_backend.sh
```

**Option C: With virtual environment**
```bash
cd /home/user/claud-appoimnet
source venv/bin/activate  # or source env/bin/activate
python manage.py runserver 8000
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### Step 2: Update Frontend API Endpoints

Since we removed all template routes, your frontend needs to use the new REST API endpoints.

---

## API Endpoint Mapping

### Old vs New Endpoints

| Old Endpoint (REMOVED) | New REST API Endpoint | Method |
|------------------------|----------------------|--------|
| `GET /` | No longer exists | - |
| `GET /chatbot/` | No longer exists | - |
| `GET /voice-assistant/` | No longer exists | - |
| `POST /api/chatbot/` | `POST /api/chatbot/` | ✅ Still works |
| `POST /api/voice/` | `POST /api/voice/` | ✅ Still works |
| `POST /api/voice-assistant/` | `POST /api/voice-assistant/` | ✅ Still works |

### Admin Panel Endpoints

| Old Endpoint (REMOVED) | New REST API Endpoint | Method |
|------------------------|----------------------|--------|
| `GET /admin-panel/` | `GET /admin-panel/api/dashboard/` | Changed |
| `GET /admin-panel/appointments/` | `GET /admin-panel/api/appointments/` | Changed |
| `GET /admin-panel/appointments/{id}/` | `GET /admin-panel/api/appointments/{booking_id}/` | Changed |
| `POST /admin-panel/appointments/{id}/update/` | `PUT /admin-panel/api/appointments/{booking_id}/update/` | Changed |
| `GET /admin-panel/calendar/` | `GET /admin-panel/api/calendar/` | Changed |
| `GET /admin-panel/api/appointments-by-date/` | `GET /admin-panel/api/appointments-by-date/` | ✅ Still works |

---

## Frontend Code Updates Required

### 1. Update API Base URL

Make sure your frontend is pointing to the correct backend:

```javascript
// frontend config or .env file
const API_BASE_URL = 'http://127.0.0.1:8000';
```

### 2. Update Chatbot Integration

**Before:**
```javascript
// This will fail - route removed
window.location.href = '/chatbot/';
```

**After:**
```javascript
// Use API endpoint
fetch('http://127.0.0.1:8000/api/chatbot/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'I need an appointment',
    session_id: sessionId
  })
})
.then(response => response.json())
.then(data => {
  console.log(data);
  // Handle response
});
```

### 3. Update Voice Assistant

**Before:**
```javascript
// This will fail - route removed
window.location.href = '/voice-assistant/';
```

**After:**
```javascript
// Use API endpoint
fetch('http://127.0.0.1:8000/api/voice-assistant/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: userMessage,
    session_id: sessionId
  })
})
.then(response => response.json())
.then(data => {
  console.log(data);
  // Handle response
});
```

### 4. Update Admin Panel Calls

**Before:**
```javascript
// Old endpoint
fetch('/admin-panel/appointments/')
```

**After:**
```javascript
// New REST API endpoint with pagination
fetch('http://127.0.0.1:8000/admin-panel/api/appointments/?page=1&page_size=20')
  .then(response => response.json())
  .then(data => {
    console.log(data.appointments);
    console.log(`Total: ${data.count}, Page: ${data.page}/${data.total_pages}`);
  });
```

---

## Common Frontend Issues & Fixes

### Issue 1: "Cannot connect to backend"

**Problem:** Backend server not running

**Solution:**
```bash
python manage.py runserver 8000
```

### Issue 2: CORS Error in Browser Console

**Problem:** Frontend on different port being blocked

**Solution:** ✅ Already fixed! CORS now allows `localhost:8080`

Check browser console for:
```
Access-Control-Allow-Origin
```

### Issue 3: 404 Not Found

**Problem:** Trying to access removed template routes

**Solution:** Update frontend to use new API endpoints (see mapping above)

### Issue 4: Empty Response or 500 Error

**Problem:** Database not migrated or data missing

**Solution:**
```bash
python manage.py migrate
python manage.py createsuperuser  # Create admin user
python setup_sample_data.py  # Load sample data
```

---

## Testing Backend Connection

### 1. Health Check

Open browser or use curl:
```bash
curl http://127.0.0.1:8000/api/health/
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "message": "Medical Appointment Booking API is running"
}
```

### 2. API Documentation

Check available endpoints:
```bash
curl http://127.0.0.1:8000/api/docs/
```

### 3. Test Chatbot API

```bash
curl -X POST http://127.0.0.1:8000/api/chatbot/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need an appointment",
    "session_id": "test-123"
  }'
```

---

## Frontend Environment Configuration

### React (.env file)

```env
REACT_APP_API_BASE_URL=http://127.0.0.1:8000
REACT_APP_API_CHATBOT=/api/chatbot/
REACT_APP_API_VOICE=/api/voice/
REACT_APP_API_VOICE_ASSISTANT=/api/voice-assistant/
```

### Vue (.env file)

```env
VUE_APP_API_BASE_URL=http://127.0.0.1:8000
VUE_APP_API_CHATBOT=/api/chatbot/
VUE_APP_API_VOICE=/api/voice/
VUE_APP_API_VOICE_ASSISTANT=/api/voice-assistant/
```

### Angular (environment.ts)

```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'http://127.0.0.1:8000',
  endpoints: {
    chatbot: '/api/chatbot/',
    voice: '/api/voice/',
    voiceAssistant: '/api/voice-assistant/'
  }
};
```

---

## Complete Frontend API Client Example

```javascript
class APIClient {
  constructor() {
    this.baseURL = 'http://127.0.0.1:8000';
  }

  async sendChatMessage(message, sessionId = null) {
    const response = await fetch(`${this.baseURL}/api/chatbot/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId
      })
    });
    return response.json();
  }

  async transcribeAudio(audioData, format = 'webm') {
    const response = await fetch(`${this.baseURL}/api/voice/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action: 'transcribe',
        audio_data: audioData,
        audio_format: format
      })
    });
    return response.json();
  }

  async synthesizeSpeech(text, language = 'en-IN') {
    const response = await fetch(`${this.baseURL}/api/voice/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        action: 'synthesize',
        text: text,
        language: language
      })
    });
    return response.json();
  }

  async getAppointments(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(
      `${this.baseURL}/admin-panel/api/appointments/?${params}`
    );
    return response.json();
  }
}

// Usage
const api = new APIClient();

// Send chat message
api.sendChatMessage('I need an appointment', 'session-123')
  .then(data => console.log(data));

// Get appointments
api.getAppointments({ status: 'pending', page: 1 })
  .then(data => console.log(data.appointments));
```

---

## Quick Checklist

Before your frontend can connect:

- [ ] Backend server is running on port 8000
- [ ] CORS is configured (✅ already done)
- [ ] Frontend is using correct API endpoints
- [ ] Frontend base URL points to `http://127.0.0.1:8000`
- [ ] Database is migrated
- [ ] No 404 errors for API endpoints

---

## Next Steps

1. **Start Backend:** Run `python manage.py runserver 8000`
2. **Test Health Check:** Visit `http://127.0.0.1:8000/api/health/`
3. **Update Frontend:** Replace template routes with API endpoints
4. **Test Integration:** Make API calls from frontend

---

## Need Help?

1. **API Documentation:** http://127.0.0.1:8000/api/docs/
2. **Full API Guide:** See `REST_API_DOCUMENTATION.md`
3. **Backend Logs:** Check Django console for errors
4. **Browser Console:** Check for CORS or network errors

The backend is now properly configured to accept requests from your frontend on port 8080!
