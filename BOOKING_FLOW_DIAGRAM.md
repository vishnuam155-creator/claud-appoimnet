# Appointment Booking Flow - Visual Guide

## 🎯 High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Patient Journey                           │
└─────────────────────────────────────────────────────────────────┘

                        Landing Page
                             ↓
                    [home.html] 🏥
                        ↓
                  Click "Book Now"
                        ↓
        ┌───────────────────────────────────┐
        │      Chatbot Interface             │
        │   [chatbot.html - Single Page]     │
        │                                    │
        │  Input: Text message (no audio)   │
        │  Output: Bot responses + Buttons  │
        └───────────────────────────────────┘
                        ↓
            JavaScript POST to API
                        ↓
        /api/chatbot/ (ChatbotAPIView)
                        ↓
   ConversationManager.process_message()
```

---

## 📋 Seven-Stage Booking Flow

```
Stage 1: GREETING
├─ Check for existing appointments
├─ Show context if found
└─ Ask symptoms OR show specialization options
    ↓
Stage 2: SYMPTOMS
├─ Parse user input
├─ Call ClaudeService.analyze_symptoms() [AI]
├─ Match to specialization
└─ Show available doctors
    ↓
Stage 3: DOCTOR SELECTION
├─ Validate selected doctor
├─ Get doctor's schedules
└─ Show available dates
    ↓
Stage 4: DATE SELECTION
├─ Validate date
├─ Get available time slots
└─ Show time options
    ↓
Stage 5: TIME SELECTION
├─ Validate time slot
├─ Store appointment_date and appointment_time
└─ Ask for patient details
    ↓
Stage 6: PATIENT DETAILS
├─ AI extracts: name, phone, email from natural language
├─ Normalize phone number (add +91 for India)
├─ Validate required fields
└─ Show confirmation
    ↓
Stage 7: CONFIRMATION
├─ Create Appointment in database
├─ Create PatientRecord (legacy table)
├─ Create AppointmentHistory (audit trail)
├─ Send SMS via Twilio
├─ Generate Booking ID (APT + 8-char UUID)
└─ Display success with booking details
```

---

## 🔄 Intent Detection System

```
User Input
    ↓
ConversationManager.process_message()
    ├─ If stage == 'greeting': _handle_greeting()
    │
    └─ Else:
        ├─ Call claude.detect_intent()
        │
        ├─ Intent == "proceed"
        │   └─ Normal stage handling
        │
        ├─ Intent == "change_doctor"
        │   └─ Go back to doctor selection
        │
        ├─ Intent == "change_date"
        │   └─ Go back to date selection
        │
        ├─ Intent == "change_time"
        │   └─ Go back to time selection
        │
        ├─ Intent == "go_back"
        │   └─ Go to previous stage
        │
        ├─ Intent == "clarify"
        │   └─ Provide help/guidance
        │
        └─ Intent == "cancel"
            └─ Cancel booking process
```

---

## 🗄️ Database Schema Relationships

```
                    ┌──────────────────┐
                    │  Specialization  │
                    ├──────────────────┤
                    │ id (PK)          │
                    │ name             │
                    │ keywords         │
                    └────────┬─────────┘
                             │
                             │ (1:N)
                             ↓
    ┌────────────────────────────────────────────┐
    │           Doctor                            │
    ├────────────────────────────────────────────┤
    │ id (PK)                                    │
    │ name                                       │
    │ email, phone                               │
    │ specialization_id (FK)                     │
    │ consultation_fee                           │
    └────────┬──────────────────────┬───────────┘
             │                      │
             │ (1:N)               │ (1:N)
             ↓                      ↓
    ┌────────────────────┐   ┌─────────────────┐
    │ DoctorSchedule     │   │ Appointment     │
    ├────────────────────┤   ├─────────────────┤
    │ id (PK)            │   │ id (PK)         │
    │ doctor_id (FK)     │   │ doctor_id (FK)  │
    │ day_of_week        │   │ patient_name    │
    │ start_time         │   │ patient_phone   │
    │ end_time           │   │ appointment_date│
    │ slot_duration      │   │ appointment_time│
    └────────────────────┘   │ booking_id      │
                             │ status          │
                             │ symptoms        │
                             └────┬────────────┘
                                  │
                                  │ (1:N)
                                  ↓
                    ┌──────────────────────────┐
                    │ AppointmentHistory       │
                    ├──────────────────────────┤
                    │ id (PK)                  │
                    │ appointment_id (FK)      │
                    │ action                   │
                    │ changed_by               │
                    │ timestamp                │
                    └──────────────────────────┘
                                  
                                  ↓ (parallel)
                    
                    ┌──────────────────────────┐
                    │ SMSNotification          │
                    ├──────────────────────────┤
                    │ id (PK)                  │
                    │ appointment_id (FK)      │
                    │ phone_number             │
                    │ message_body             │
                    │ status (sent/delivered)  │
                    │ message_sid (Twilio)     │
                    └──────────────────────────┘
```

---

## 🤖 AI/LLM Integration Points

```
User Input
    ↓
┌─────────────────────────────────────────────────────┐
│         ClaudeService (claude_service.py)            │
│        (Currently: Gemini 2.5-flash)                 │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. analyze_symptoms(symptoms_text)                 │
│     └─ Input: "I have leg pain and swelling"        │
│        Output: {specialization: "Orthopedic", ...}  │
│                                                      │
│  2. detect_intent(message, stage, context)          │
│     └─ Input: "Actually, I want a different doctor" │
│        Output: {intent: "change_doctor", ...}       │
│                                                      │
│  3. extract_information(text, info_type)            │
│     └─ Input: "My name is John, 9876543210"         │
│        Output: {name: "John", phone: "9876543210"}  │
│                                                      │
│  4. generate_conversational_response(...)           │
│     └─ Input: User message + context                │
│        Output: Natural bot response                 │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 📱 Chat Interface Components

```
┌──────────────────────────────────────────────┐
│          Chat Header                          │
│  🏥 AI Medical Assistant                      │
│  "Helping you book appointments smarter"     │
└──────────────────────────────────────────────┘
│                                               │
│  Messages Area                                │
│  ┌─────────────────────────────────────────┐ │
│  │ [Bot] Hello! I'm your AI assistant      │ │
│  │ [Bot] How can I help you today?         │ │
│  │                                          │ │
│  │                   [User] I have leg pain│ │
│  │                                          │ │
│  │ [Bot] Based on your symptoms...         │ │
│  │ [Bot Typing: ...]                       │ │
│  └─────────────────────────────────────────┘ │
│                                               │
│  Quick Options                                │
│  [Button] Dr. John Smith   [Button] Dr. Jane │
│  [Button] Skip             [Button] Other...  │
│                                               │
│  Input Area                                   │
│  [____________ Type message...  ] [Send]     │
└──────────────────────────────────────────────┘
```

---

## 📊 State Management

```
Session Cache (timeout: 1 hour)

session_{session_id} = {
  "stage": "symptoms",              # Current stage
  "conversation_history": [         # Full history
    {
      "role": "user",
      "content": "I have leg pain",
      "timestamp": "2025-11-10T..."
    },
    {
      "role": "assistant",
      "content": "Let me help...",
      "timestamp": "2025-11-10T..."
    }
  ],
  "data": {                         # Collected data
    "symptoms": "leg pain",
    "suggested_specialization": "Orthopedic",
    "doctor_id": 5,
    "appointment_date": "2025-11-15",
    "appointment_time": "14:30",
    "patient_name": "John Doe",
    "patient_phone": "+919876543210",
    "patient_email": "john@example.com"
  },
  "timestamp": "2025-11-10T..."
}
```

---

## 🔐 Communication Channels

```
Patient                    System              External Services
  │                          │                        │
  ├─ Web Chat Interface       │                        │
  │                    POST /api/chatbot/              │
  │                          ├─────────────────────────┤
  │                          │ Google Gemini API       │
  │                          │ (analyze_symptoms)      │
  │                          ├─────────────────────────┤
  │                          │ Database                │
  │                          │ (save appointment)      │
  │                          ├─────────────────────────┤
  │                          │ Twilio SMS Service      │
  │                          │ (send confirmation SMS) │
  │                      ↓   ├─────────────────────────┤
  │ ← JSON Response          │ Patient Phone (SMS)     │
  │   Update Chat UI         │                        │
  │
  ├─ WhatsApp                │
  │                          │ (Alternative channel)
```

---

## 🎯 Key Integration Points

### Frontend Integration
- **File:** `/home/user/claud-appoimnet/templates/patient_booking/chatbot.html`
- **Technology:** Vanilla JavaScript + HTML + CSS
- **API Call:** Fetch POST to `/api/chatbot/`
- **State Management:** Session ID in browser

### Backend Integration
- **Entry Point:** `/home/user/claud-appoimnet/patient_booking/views.py - ChatbotAPIView`
- **Core Logic:** `/home/user/claud-appoimnet/chatbot/conversation_manager.py`
- **AI Service:** `/home/user/claud-appoimnet/chatbot/claude_service.py`
- **SMS Service:** `/home/user/claud-appoimnet/twilio_service.py`

### Database Integration
- **Models:** `/home/user/claud-appoimnet/appointments/models.py`
- **Doctor Data:** `/home/user/claud-appoimnet/doctors/models.py`

---

## 🚀 Voice Integration Entry Points

### Where Voice Would Fit

```
Stage 2: SYMPTOMS
Current: User types "I have leg pain"
Future:  User clicks 🎤 and says "I have leg pain"
         ↓ (Web Speech API)
         Speech-to-Text converts to text
         ↓
         Proceed as normal

Stage 7: CONFIRMATION
Current: Bot shows "Your appointment is confirmed!"
Future:  Bot shows message + plays audio with speaker 🔊
         ↓ (Text-to-Speech)
         User hears confirmation

New Feature: Voice Confirmation
         Bot: "Please say yes to confirm"
         User: Says "yes"
         ↓ (Web Speech API)
         Confirmation recorded and processed
```

### Files to Modify for Voice
1. `templates/patient_booking/chatbot.html` - Add mic/speaker buttons
2. `patient_booking/views.py` - Add audio endpoints
3. `chatbot/conversation_manager.py` - Handle voice input
4. `static/js/voice_handler.js` - Client-side voice handling (new)
5. `chatbot/voice_service.py` - Backend voice processing (new)

---

## 📈 Performance Considerations

### Current Bottlenecks
- **AI Response Time:** Gemini API calls can take 1-3 seconds
- **Database Queries:** Multiple DB calls per stage transition
- **SMS Sending:** Twilio API calls are async but blocking appointment creation

### For Voice Integration
- **Audio Upload:** Larger payloads (reduce with compression)
- **Speech Processing:** Real-time transcription needs streaming
- **TTS Playback:** Audio latency affects user experience

---

**Generated:** 2025-11-10  
**Status:** Ready for voice system integration
