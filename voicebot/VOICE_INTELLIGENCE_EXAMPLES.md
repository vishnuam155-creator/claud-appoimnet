# Voice Intelligence Assistant - Usage Examples

This document demonstrates how the Voice Intelligence Assistant works with real examples.

## System Overview

The Voice Intelligence Assistant is designed to:
1. **Understand** any user voice query (even noisy or incomplete speech)
2. **Identify** the user's intent
3. **Convert** user speech into structured JSON actions for the backend
4. **Query** the database when needed
5. **Generate** clear natural-language spoken replies

---

## Architecture Flow

```
User Voice Input
    ↓
[Voice Understanding & Correction]
    ↓
[Intent Identification]
    ↓
[JSON Action Generation]
    ↓
[Database Execution] ← Backend processes the JSON action
    ↓
[Natural Language Response Generation]
    ↓
Voice Output to User
```

---

## API Endpoints

### 1. Main Voice Intelligence Endpoint
**POST** `/voicebot/api/intelligence/`

Processes voice input end-to-end (understanding → intent → action → DB → response).

### 2. Database Action Endpoint
**POST** `/voicebot/api/database-action/`

Executes database actions directly (for backend integration).

### 3. Intent Analysis Endpoint
**POST** `/voicebot/api/intent-analysis/`

Analyzes intent and generates actions WITHOUT executing (for debugging).

### 4. Session Management Endpoint
**GET/DELETE** `/voicebot/api/session/?session_id=xxx`

Manages conversation sessions.

### 5. Compatibility Endpoint
**POST** `/voicebot/api/v2/`

Legacy-compatible endpoint using the new system.

---

## Example Use Cases

### Example 1: Appointment Booking

#### User says:
```
"Hey, I want to book appointment tomorrow morning with Dr. Rahul"
```

#### Step 1: Voice Understanding
```json
{
  "corrected_text": "I want to book appointment tomorrow morning with Dr. Rahul",
  "detected_language": "en",
  "extracted_entities": {
    "doctor_name": "Dr. Rahul",
    "date": "tomorrow",
    "time": "morning"
  },
  "confidence": "high",
  "needs_clarification": false
}
```

#### Step 2: Intent Identification
```json
{
  "intent": "appointment_booking",
  "sub_intent": "create",
  "confidence": "high",
  "requires_database": true,
  "extracted_params": {
    "doctor_name": "Dr. Rahul",
    "date": "tomorrow",
    "time": "morning"
  }
}
```

#### Step 3: JSON Action Generated
```json
{
  "action": "query_database",
  "query_type": "create_appointment",
  "parameters": {
    "doctor_name": "Dr. Rahul",
    "date": "2025-11-14",
    "time": "10:00 AM"
  }
}
```

#### Step 4: Database Result
```json
{
  "status": "success",
  "message": "Appointment created successfully",
  "data": {
    "appointment_id": 123,
    "booking_id": "APT000123",
    "doctor_name": "Rahul Kumar",
    "appointment_date": "2025-11-14",
    "appointment_time": "10:00 AM",
    "status": "confirmed"
  }
}
```

#### Step 5: Voice Response
```
"Excellent news! Your appointment with Dr. Rahul Kumar is confirmed for tomorrow at 10:00 AM.
Your booking ID is APT000123. You'll receive a confirmation message on your phone.
Is there anything else I can help you with?"
```

---

### Example 2: Appointment Lookup

#### User says:
```
"Check my appointment with phone 9876543210"
```

#### JSON Action Generated:
```json
{
  "action": "query_database",
  "query_type": "appointment_lookup",
  "parameters": {
    "phone": "9876543210"
  }
}
```

#### Backend Returns:
```json
{
  "status": "success",
  "message": "Found 1 appointment(s)",
  "data": [
    {
      "appointment_id": 123,
      "booking_id": "APT000123",
      "doctor_name": "Rahul Kumar",
      "appointment_date": "2025-11-14",
      "appointment_time": "10:00 AM",
      "status": "confirmed"
    }
  ]
}
```

#### Voice Response:
```
"I found your appointment with Dr. Rahul Kumar on tomorrow at 10:00 AM. The status is confirmed.
Would you like to reschedule or cancel this appointment?"
```

---

### Example 3: Mixed Language Input (Indian English)

#### User says (with Malayalam/Hindi mix):
```
"Nale morning Doctor Rahul inte koode appointment veno"
```
(Translation: Want appointment tomorrow morning with Doctor Rahul)

#### Voice Understanding (Corrected):
```json
{
  "corrected_text": "I want appointment tomorrow morning with Doctor Rahul",
  "detected_language": "mixed",
  "extracted_entities": {
    "doctor_name": "Doctor Rahul",
    "date": "tomorrow",
    "time": "morning"
  },
  "confidence": "medium"
}
```

The system corrects the mixed language input to standard English and proceeds normally.

---

### Example 4: Noisy/Incomplete Speech

#### User says (unclear audio):
```
"um... uh... book... doctor... nine eight seven... tomorrow?"
```

#### Voice Understanding (Corrected):
```json
{
  "corrected_text": "book doctor appointment tomorrow",
  "detected_language": "en",
  "extracted_entities": {
    "date": "tomorrow"
  },
  "confidence": "low",
  "needs_clarification": true
}
```

#### Voice Response (Clarification):
```
"I understand you'd like to book an appointment for tomorrow.
Which doctor would you like to see?"
```

---

### Example 5: Cancel Appointment

#### User says:
```
"Cancel my appointment, booking ID is APT000123"
```

#### JSON Action:
```json
{
  "action": "query_database",
  "query_type": "cancel_appointment",
  "parameters": {
    "appointment_id": 123,
    "phone": "9876543210"
  }
}
```

#### Backend Result:
```json
{
  "status": "success",
  "message": "Appointment cancelled successfully",
  "data": {
    "appointment_id": 123,
    "booking_id": "APT000123"
  }
}
```

#### Voice Response:
```
"Your appointment has been cancelled successfully.
Is there anything else I can help you with?"
```

---

### Example 6: Doctor Search by Symptoms

#### User says:
```
"I have fever and headache, which doctor should I see?"
```

#### JSON Action:
```json
{
  "action": "query_database",
  "query_type": "get_doctor_by_symptoms",
  "parameters": {
    "symptoms": ["fever", "headache"]
  }
}
```

#### Backend Result:
```json
{
  "status": "success",
  "message": "Recommended 2 doctor(s) for your symptoms",
  "data": {
    "doctors": [
      {
        "id": 1,
        "name": "Rahul Kumar",
        "specialization": "General Physician",
        "consultation_fee": "500"
      },
      {
        "id": 5,
        "name": "Priya Sharma",
        "specialization": "Internal Medicine",
        "consultation_fee": "600"
      }
    ]
  }
}
```

#### Voice Response:
```
"I found 2 doctors for you.
1. Dr. Rahul Kumar, General Physician.
2. Dr. Priya Sharma, Internal Medicine.
Which doctor would you prefer?"
```

---

## API Request/Response Examples

### Complete Voice Processing

**Request:**
```bash
curl -X POST http://localhost:8000/voicebot/api/intelligence/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "Book appointment tomorrow 10 AM with Dr. Rahul",
    "session_id": "optional-session-id"
  }'
```

**Response:**
```json
{
  "success": true,
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "voice_response": "Excellent news! Your appointment with Dr. Rahul is confirmed for tomorrow at 10:00 AM...",
  "action": "database_query_completed",
  "data": {
    "intent": {
      "intent": "appointment_booking",
      "confidence": "high",
      "requires_database": true
    },
    "database_action": {
      "action": "query_database",
      "query_type": "create_appointment",
      "parameters": {...}
    },
    "database_result": {
      "status": "success",
      "data": {...}
    },
    "conversation_context": {
      "session_id": "...",
      "collected_information": {...}
    }
  }
}
```

---

### Direct Database Action Execution

**Request:**
```bash
curl -X POST http://localhost:8000/voicebot/api/database-action/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "query_database",
    "query_type": "appointment_lookup",
    "parameters": {
      "phone": "9876543210"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "session_id": "...",
  "voice_response": "I found your appointment with Dr. Rahul Kumar on tomorrow at 10:00 AM...",
  "database_result": {
    "status": "success",
    "message": "Found 1 appointment(s)",
    "data": [...]
  }
}
```

---

### Intent Analysis (Testing)

**Request:**
```bash
curl -X POST http://localhost:8000/voicebot/api/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "I want to check my appointment"
  }'
```

**Response:**
```json
{
  "understood_input": {
    "corrected_text": "I want to check my appointment",
    "detected_language": "en",
    "extracted_entities": {},
    "confidence": "high"
  },
  "intent": {
    "intent": "appointment_lookup",
    "confidence": "high",
    "requires_database": true
  },
  "database_action": {
    "action": "query_database",
    "query_type": "appointment_lookup",
    "parameters": {}
  },
  "missing_information": ["phone"]
}
```

---

## Key Features

### 1. Voice Understanding with Error Correction
- Corrects spelling mistakes
- Handles incomplete speech
- Converts mixed language inputs to standard English
- Extracts entities accurately

### 2. Multi-Language Support
- English (standard, Indian-style)
- Hindi mixed speech
- Malayalam mixed speech
- Tamil mixed speech

### 3. Intent Recognition
Supported intents:
- `appointment_booking` - Create new appointment
- `appointment_lookup` - Check existing appointment
- `appointment_cancel` - Cancel appointment
- `appointment_reschedule` - Change appointment date/time
- `doctor_query` - Ask about doctors
- `general_query` - General questions
- `support_request` - Help requests

### 4. Database Query Types
- `create_appointment` - Book new appointment
- `appointment_lookup` - Find appointments
- `cancel_appointment` - Cancel appointment
- `reschedule_appointment` - Reschedule appointment
- `get_doctors` - List doctors
- `get_doctor_by_symptoms` - Recommend doctors by symptoms
- `check_availability` - Check available slots

### 5. Natural Language Response Generation
- Friendly, conversational tone
- Context-aware responses
- Clear explanations
- Follow-up questions

---

## Session Management

### Get Session Info
```bash
curl http://localhost:8000/voicebot/api/session/?session_id=xxx
```

**Response:**
```json
{
  "session_id": "...",
  "conversation_length": 5,
  "collected_information": {
    "name": "John Doe",
    "phone": "9876543210",
    "doctor_name": "Dr. Rahul",
    "appointment_id": 123
  },
  "current_intent": "appointment_booking",
  "last_action": "appointment_created"
}
```

### Clear Session
```bash
curl -X DELETE http://localhost:8000/voicebot/api/session/?session_id=xxx
```

---

## Integration with Frontend

### JavaScript Example

```javascript
async function sendVoiceMessage(voiceText, sessionId = null) {
  const response = await fetch('/voicebot/api/intelligence/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      voice_text: voiceText,
      session_id: sessionId
    })
  });

  const data = await response.json();

  // Speak the response using Web Speech API
  const utterance = new SpeechSynthesisUtterance(data.voice_response);
  speechSynthesis.speak(utterance);

  // Store session ID for continuity
  return data.session_id;
}

// Usage
let sessionId = null;

// User speaks: "Book appointment tomorrow"
sessionId = await sendVoiceMessage("Book appointment tomorrow", sessionId);

// User speaks: "With Dr. Rahul"
sessionId = await sendVoiceMessage("With Dr. Rahul", sessionId);

// User speaks: "10 AM"
sessionId = await sendVoiceMessage("10 AM", sessionId);
```

---

## Error Handling

### Missing Information
```json
{
  "success": true,
  "action": "clarification_needed",
  "voice_response": "Could you please provide your phone number?",
  "data": {
    "missing_information": ["phone"]
  }
}
```

### Database Error
```json
{
  "success": false,
  "action": "error",
  "voice_response": "I'm sorry, that time slot is not available. Would you like me to suggest alternative times?",
  "data": {
    "database_result": {
      "status": "error",
      "message": "Selected time slot is not available"
    }
  }
}
```

### Low Confidence Understanding
```json
{
  "success": true,
  "action": "clarification_needed",
  "voice_response": "I didn't quite catch that. Could you please repeat?",
  "data": {
    "understood_input": {
      "confidence": "low",
      "needs_clarification": true
    }
  }
}
```

---

## Behavior Rules

1. **Always respond with either:**
   - JSON action (when DB interaction needed) OR
   - Spoken natural response (when DB data provided)

2. **Never fabricate data** that must come from DB

3. **Use simple English** suitable for phone calls

4. **Be polite, patient, and helpful**

5. **Correct errors automatically** without bothering the user

6. **Handle mixed languages** seamlessly

7. **Ask for clarification** when uncertain

---

## System Prompt Summary

The Voice Intelligence Assistant operates with these core principles:

✅ **Understand** - Correct errors, handle mixed languages, extract entities
✅ **Identify** - Detect user intent with high accuracy
✅ **Convert** - Generate structured JSON for backend
✅ **Query** - Execute database operations when needed
✅ **Respond** - Generate clear, natural voice responses

This creates a natural, human-like conversational experience for voice-based appointment booking.
