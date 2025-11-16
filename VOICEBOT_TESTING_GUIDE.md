# VoiceBot RAG API - Postman/cURL Testing Guide

## 🔧 Base Configuration

**Base URL:** `http://localhost:8000` (or your server URL)
**Endpoint:** `/voicebot/api/`
**Method:** `POST`
**Content-Type:** `application/json`

---

## 📝 Complete Booking Flow Test Cases

### 1️⃣ Start Conversation (Get Greeting)

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": ""
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "voice_abc123...",
  "message": "Hello! Welcome to MedCare Clinic. I'm here to help you book an appointment. May I have your name, please?",
  "stage": "patient_name",
  "action": "continue",
  "data": {
    "stage": "patient_name",
    "patient_name": null,
    "patient_phone": null,
    "doctor_id": null,
    "doctor_name": null,
    "appointment_date": null,
    "appointment_time": null,
    "appointment_id": null,
    "completed": false
  }
}
```

**⚠️ IMPORTANT:** Copy the `session_id` from the response and use it in all subsequent requests!

---

### 2️⃣ Provide Patient Name

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is John Smith",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "session_id": "voice_abc123...",
  "message": "Nice to meet you, John Smith! How can I help you today? You can tell me which doctor you'd like to see, or describe any symptoms you're experiencing.",
  "stage": "doctor_selection",
  "action": "continue",
  "data": {
    "stage": "doctor_selection",
    "patient_name": "John Smith",
    ...
  }
}
```

---

### 3️⃣ Option A: Select Doctor by Name

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to see Dr. Michael Brown",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

---

### 3️⃣ Option B: Describe Symptoms (AI Recommendation)

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a severe headache and dizziness",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "I understand you're experiencing a severe headache and dizziness. Based on your symptoms, I recommend seeing a Neurologist. We have Dr. Smith who specializes in this area. Would you like to book with Dr. Smith?",
  "stage": "doctor_selection",
  "action": "continue",
  ...
}
```

**Then confirm:**
```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Yes, book Dr. Smith",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

---

### 4️⃣ Select Appointment Date

```bash
# Option 1: Natural language
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tomorrow",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'

# Option 2: Day of week
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Next Monday",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'

# Option 3: Specific date
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "December 20th",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Perfect! Tomorrow works. The doctor has several time slots available: 10:00 AM, 2:00 PM, and 4:30 PM. Which time would be most convenient for you?",
  "stage": "time_selection",
  "action": "continue",
  ...
}
```

---

### 5️⃣ Select Time Slot

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "10 AM",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Excellent! I've reserved 10:00 AM for you. Now, I'll need your phone number so we can send you a confirmation message. What's your 10-digit mobile number?",
  "stage": "phone_collection",
  "action": "continue",
  ...
}
```

---

### 6️⃣ Provide Phone Number

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "9876543210",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Perfect! Let me confirm your appointment details. Your name is John Smith. You're booking with Dr. Smith, who is a Neurologist. The appointment is on November 17, 2025 at 10:00 AM. Your phone number is 98765 43210. Is everything correct?",
  "stage": "confirmation",
  "action": "continue",
  ...
}
```

---

### 7️⃣ Confirm Booking

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Yes, confirm it",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Perfect! Your appointment is confirmed! Your booking ID is APT12345ABC. You'll receive an SMS confirmation shortly at 9876543210. To recap: you have an appointment with Dr. Smith on November 17, 2025 at 10:00 AM. Is there anything else I can help you with today?",
  "stage": "completed",
  "action": "booking_complete",
  "data": {
    "appointment_id": 123,
    "booking_id": "APT12345ABC",
    "completed": true,
    ...
  }
}
```

---

## 🔄 Dynamic Change Scenarios

### Change Doctor After Selection

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Actually, I want to see a different doctor",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** System returns to doctor selection stage.

---

### Change Date After Selecting Time

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Can I change the date to next week?",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** System clears date/time and returns to date selection.

---

### Change Time Slot

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I prefer afternoon slots instead",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** System shows afternoon time slots.

---

### Change Phone at Confirmation

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Wait, my number is 1234567890",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** System updates phone number and re-confirms details.

---

### Cancel Booking

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Cancel the booking",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "I understand. Your booking has been cancelled. If you'd like to book an appointment later, just let me know. Is there anything else I can help you with?",
  "stage": "completed",
  "action": "cancelled",
  ...
}
```

---

## 🧪 Edge Case Testing

### Test Unavailable Slot

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want an appointment today at 3 PM",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** System checks availability, suggests alternatives if unavailable.

---

### Test Multiple Symptom Analysis

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have chest pain, shortness of breath, and high blood pressure",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

**Expected:** Recommends Cardiologist.

---

### Test Natural Date Parsing

```bash
# Test "day after tomorrow"
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "day after tomorrow",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'

# Test "this Friday"
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "this Friday",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'

# Test specific date format
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "November 25th, 2025",
    "session_id": "YOUR_SESSION_ID_HERE"
  }'
```

---

## 📊 API Information Endpoint

```bash
# Get API documentation
curl -X GET http://localhost:8000/voicebot/api/
```

**Expected:** Returns comprehensive API documentation JSON.

---

## 🎯 Postman Collection Setup

### Environment Variables

Create a Postman environment with:

| Variable | Initial Value | Current Value |
|----------|--------------|---------------|
| `base_url` | `http://localhost:8000` | (same) |
| `session_id` | `null` | (auto-updated from responses) |

### Pre-request Script (For Session Management)

Add this to your Postman collection pre-request script:

```javascript
// Auto-extract and save session_id from previous response
if (pm.response && pm.response.json()) {
    const response = pm.response.json();
    if (response.session_id) {
        pm.environment.set("session_id", response.session_id);
    }
}
```

### Test Script (Auto Session ID)

Add this to each request's test script:

```javascript
// Auto-save session_id from response
const response = pm.response.json();
if (response.session_id) {
    pm.environment.set("session_id", response.session_id);
    console.log("Session ID saved: " + response.session_id);
}

// Basic assertions
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success field", function () {
    pm.expect(response).to.have.property('success');
});

pm.test("Response has session_id", function () {
    pm.expect(response).to.have.property('session_id');
});
```

---

## 📋 Quick Test Sequence (Copy-Paste Ready)

Replace `YOUR_SESSION_ID` with actual session ID from first response:

```bash
# 1. Start
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": ""}'

# 2. Name (use session_id from step 1)
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "My name is John Smith", "session_id": "YOUR_SESSION_ID"}'

# 3. Symptoms
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a severe headache", "session_id": "YOUR_SESSION_ID"}'

# 4. Confirm doctor
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Yes, book it", "session_id": "YOUR_SESSION_ID"}'

# 5. Date
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Tomorrow", "session_id": "YOUR_SESSION_ID"}'

# 6. Time
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "10 AM", "session_id": "YOUR_SESSION_ID"}'

# 7. Phone
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "9876543210", "session_id": "YOUR_SESSION_ID"}'

# 8. Confirm
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Yes, confirm", "session_id": "YOUR_SESSION_ID"}'
```

---

## 🔍 Debugging Tips

### Check Conversation History

Access Django admin: `http://localhost:8000/admin/`
- Navigate to **Voicebot** > **Voice Conversations**
- Search by session_id
- View all messages in the conversation

### View Raw Response

```bash
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test_123"}' \
  -w "\n\nHTTP Status: %{http_code}\n"
```

### Enable Verbose Output

```bash
curl -v -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## ⚠️ Common Issues

### Issue: Session not persisting
**Solution:** Make sure to pass `session_id` in all requests after the first one.

### Issue: 500 Internal Server Error
**Solution:**
1. Check Django logs: `python manage.py runserver` console
2. Verify Gemini API key is set in settings
3. Check database migrations are applied

### Issue: Empty response
**Solution:** Ensure Django server is running on port 8000.

---

## 🎉 Success Indicators

✅ **Successful Booking:**
- `action: "booking_complete"`
- `stage: "completed"`
- `appointment_id` present in response
- `booking_id` present in response

✅ **Conversation Flowing:**
- Each response has a `session_id`
- `stage` progresses through: greeting → patient_name → doctor_selection → date_selection → time_selection → phone_collection → confirmation → completed

✅ **Changes Handled:**
- When you request a change, `stage` goes back to the relevant stage
- Previous data is preserved (except what you're changing)

---

**Happy Testing! 🚀**
