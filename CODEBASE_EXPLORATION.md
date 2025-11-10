# Medical Appointment System - Codebase Exploration Report

## 1. PROJECT OVERVIEW

**Project Type:** Django-based Medical Appointment Booking System with AI-powered Chatbot
**Current Branch:** `claude/add-voice-system-msg-011CUykwy7MGRn95xvE53DUk` (Adding voice system functionality)
**Technology Stack:** Django 4.2.7 + Django REST Framework

### Key Features
- AI-powered chatbot for appointment booking (Claude/Gemini)
- SMS notifications via Twilio
- WhatsApp integration
- Admin dashboard with calendar view
- Patient record management

---

## 2. TECHNOLOGY STACK

### Backend
- **Framework:** Django 4.2.7
- **API:** Django REST Framework 3.14.0
- **Database:** SQLite (development, PostgreSQL recommended for production)
- **Python Version:** 3.8+

### AI/ML
- **Primary AI:** Google Generative AI (Gemini 2.5-flash) - Currently being used
- **Alternative API:** Anthropic Claude (configured but Gemini is active)
- **API Key Storage:** Environment variables (.env)

### Communication
- **SMS:** Twilio 8.10.0 (for SMS notifications and reminders)
- **WhatsApp:** Custom WhatsApp integration (via Twilio or Meta API)
- **Email:** Ready for integration

### Frontend
- **Template Engine:** Django Templates
- **Frontend Framework:** Vanilla JavaScript (no React/Vue)
- **CSS:** Inline CSS in HTML templates
- **Chat UI:** Custom HTML/CSS/JS chat interface

### Third-party Libraries
- `requests` - HTTP requests
- `pillow` - Image processing
- `python-dotenv` - Environment configuration
- `django-cors-headers` - CORS support

---

## 3. PROJECT STRUCTURE

```
claud-appoimnet/
├── config/                      # Django main settings
│   ├── settings.py             # Main configuration
│   ├── urls.py                 # URL routing
│   └── wsgi.py
│
├── doctors/                     # Doctor management app
│   ├── models.py               # Specialization, Doctor, DoctorSchedule, DoctorLeave
│   ├── admin.py
│   └── views.py
│
├── appointments/                # Appointment management
│   ├── models.py               # Appointment, AppointmentHistory, SMSNotification
│   ├── admin.py
│   └── views.py
│
├── chatbot/                     # AI Chatbot logic (CORE BOOKING ENGINE)
│   ├── conversation_manager.py  # 1,384 lines - Main conversation flow
│   ├── claude_service.py        # AI service (Gemini integration)
│   ├── date_parser.py           # Date parsing utilities
│   ├── models.py
│   └── views.py
│
├── patient_booking/             # Patient-facing views
│   ├── models.py                # PatientRecord (separate from Appointment model)
│   ├── views.py                 # Chat API endpoint
│   ├── urls.py                  # Routes: /, /chatbot/, /api/chatbot/
│   └── models.py
│
├── admin_panel/                 # Custom admin dashboard
│   ├── views.py                 # Dashboard, calendar views
│   ├── urls.py
│   └── models.py
│
├── whatsapp_integration/        # WhatsApp communication
│   ├── whatsapp_service.py
│   ├── views.py
│   ├── models.py
│   ├── urls.py
│   └── templates/
│
├── templates/                   # HTML templates
│   ├── patient_booking/
│   │   ├── home.html            # Landing page with CTA
│   │   └── chatbot.html         # Chat interface (1,384 lines)
│   └── admin_panel/
│       └── calendar.html        # Calendar view
│
├── twilio_service.py            # SMS notification service
├── manage.py                    # Django management script
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Documentation

```

---

## 4. CURRENT APPOINTMENT BOOKING FLOW

### Flow Overview (7 Stages)

```
1. GREETING → 2. SYMPTOMS → 3. DOCTOR SELECTION → 4. DATE SELECTION 
    ↓
5. TIME SELECTION → 6. PATIENT DETAILS → 7. CONFIRMATION
```

### Stage Details

#### Stage 1: **GREETING** (`_handle_greeting()`)
- **User Interaction:** Chat message initiation
- **What Happens:**
  - System checks for existing appointments
  - If existing appointment exists: Shows appointment context with options (new booking, cancel, reschedule, details)
  - If no appointment: Asks to describe symptoms or select specialization from available options
- **Output:** Welcome message + Specialization options as buttons

#### Stage 2: **SYMPTOMS** (`_handle_symptoms()`)
- **User Interaction:** Text description of symptoms OR click specialization button
- **What Happens:**
  - If user clicked specialty button: Direct to that specialty
  - If user typed symptoms: AI analyzes using Gemini to suggest specialty
  - Queries database for available doctors in suggested specialty
- **AI Integration:** `claude.analyze_symptoms()` uses Gemini to match symptoms to specialization
- **Output:** List of available doctors as clickable options

#### Stage 3: **DOCTOR SELECTION** (`_handle_doctor_selection()`)
- **User Interaction:** Click doctor name or type doctor name
- **What Happens:**
  - Validate selected doctor exists and is active
  - Retrieve doctor's available dates (next 7 days)
- **Output:** Available dates as clickable buttons

#### Stage 4: **DATE SELECTION** (`_handle_date_selection()`)
- **User Interaction:** Click date or type date
- **What Happens:**
  - Validate date availability
  - Fetch available time slots for selected doctor on that date
  - Filter out already booked slots
- **Output:** Available time slots as clickable buttons

#### Stage 5: **TIME SELECTION** (`_handle_time_selection()`)
- **User Interaction:** Click time slot or type time
- **What Happens:**
  - Validate time slot availability
  - Store appointment_date and appointment_time in session state
- **Output:** Patient details form prompt

#### Stage 6: **PATIENT DETAILS** (`_handle_patient_details()`)
- **User Interaction:** Enter patient name, phone, email
- **What Happens:**
  - Extract name, phone, email from user message using AI
  - AI uses Gemini to intelligently extract info from natural language
  - Validate required fields (name, phone)
  - Normalize phone number (add +91 for India if missing)
- **Validation:** E.164 phone format, 10+ digit number
- **Output:** Confirmation message with all booking details

#### Stage 7: **CONFIRMATION** (`_handle_confirmation()`)
- **User Interaction:** Confirm booking or modify details
- **What Happens:**
  1. Create `Appointment` record in database
  2. Create `PatientRecord` record (separate table for legacy compatibility)
  3. Create `AppointmentHistory` record (tracks creation)
  4. **Send SMS confirmation** via Twilio to patient's phone
  5. Generate unique Booking ID (format: `APT{8-char-uuid}`)
- **SMS Content:** Doctor name, date, time, booking ID, instructions
- **Output:** Success message with booking ID and appointment details

### Intent Detection & Flow Control
The chatbot can understand user intentions across all stages:
- **proceed** - User provides requested information normally
- **change_doctor** - User wants to select different doctor
- **change_date** - User wants different date
- **change_time** - User wants different time
- **go_back** - User wants to return to previous step
- **clarify** - User asks for help/clarification
- **cancel** - User wants to cancel booking process

### State Management
- **Storage:** Django cache (1-hour timeout)
- **Session ID:** Generated on first message, persists across conversation
- **Conversation History:** Full message history with timestamps
- **Data Store:** Collected appointment data (symptoms, doctor_id, dates, patient info)

---

## 5. PATIENT INTERACTIONS & FORMS

### Chat Interface
- **Location:** `/chatbot/` route
- **File:** `templates/patient_booking/chatbot.html` (382 lines)
- **Type:** Single-page chat application (no page reloads)

### UI Components

#### Input Area
- Text input field with placeholder "Type your message..."
- Send button
- Auto-focus on load

#### Message Display
- Bot messages: Left-aligned, gray background
- User messages: Right-aligned, blue background
- Typing indicator: Animated dots while bot responds
- Auto-scroll to latest message

#### Options/Buttons
- Clickable buttons for quick selections (doctors, dates, times, specializations)
- Skip buttons with different styling
- Dynamically generated based on stage

#### Design Features
- Modern gradient backgrounds (purple-blue to gray)
- Smooth animations and transitions
- Responsive design (mobile-friendly)
- Message animation: Fade-in effect

### API Endpoint
- **URL:** `/api/chatbot/`
- **Method:** POST
- **Request:** `{"message": "text", "session_id": "optional"}`
- **Response:** 
  ```json
  {
    "success": true,
    "session_id": "session_...",
    "message": "Bot response text",
    "action": "action_type",
    "options": [{"label": "...", "value": "..."}],
    "booking_id": "APT12345678" (on confirmation)
  }
  ```

### Data Validation
- **Phone:** E.164 format, auto-add +91 for India
- **Email:** Standard email format (optional)
- **Date:** Must be available doctor slot
- **Name:** Required, max 200 characters

---

## 6. EXISTING VOICE/AUDIO IMPLEMENTATIONS

### Current Status: **NONE**
- ❌ No speech-to-text implementation
- ❌ No text-to-speech implementation
- ❌ No audio recording/playback
- ❌ No WebRTC integration
- ❌ No Web Audio API usage
- ❌ No voice commands

### Git Branch Insight
Current branch name: `claude/add-voice-system-msg-011CUykwy7MGRn95xvE53DUk`
- Suggests: Adding voice system message handling
- Indicates: This is an upcoming feature

### Where Voice Could Be Integrated
1. **Chat Input:** Add microphone button for speech-to-text
2. **Chat Output:** Add speaker icon for text-to-speech of bot responses
3. **Confirmation:** Voice confirmation before creating appointment
4. **SMS Alternative:** Voice call confirmations instead of SMS

---

## 7. MESSAGING & COMMUNICATION SYSTEM

### SMS (Twilio Integration)

**Service File:** `twilio_service.py` (308 lines)

**Capabilities:**
- Send appointment confirmations
- Send appointment reminders
- Send cancellation notices
- Send reschedule notices
- Track SMS delivery status

**Implementation:**
```
Appointment Created → Twilio SMS Service → Patient Phone
```

**Features:**
- Phone normalization (handles various formats)
- Automatic +91 prefix for Indian numbers
- Message template formatting
- Error tracking and logging
- SMS delivery status logging in `SMSNotification` model

**SMS Notification Model:**
- Stores: phone number, message body, Twilio SID, delivery status
- Tracks: confirmation, reminder, cancellation, reschedule
- Indexes: By appointment, message_sid, status

### WhatsApp Integration

**Service File:** `whatsapp_integration/whatsapp_service.py` (11,110 lines)

**Capabilities:**
- Chatbot conversation via WhatsApp
- Two-way messaging
- Media support (images, documents)
- Webhook for incoming messages
- Message delivery tracking

**Integration Points:**
- Separate from web chatbot (parallel system)
- Uses Twilio or Meta WhatsApp API
- Allows patients to book via WhatsApp instead of web

### Email Integration

**Status:** Ready to implement
- No current implementation
- Django email backend configured in settings
- Could send appointment details via email

### Communication Flow
```
Patient Interaction → Appointment Created → SMS/WhatsApp Notification
                  ↓
            Admin Notification (optional)
```

---

## 8. DATABASE MODELS & RELATIONSHIPS

### Key Models

#### **Appointment** (appointments/models.py)
- Patient details (name, phone, email, age, gender)
- Doctor relationship
- Appointment timing (date, time)
- Symptoms and notes
- Status (pending, confirmed, cancelled, completed, no_show)
- Unique Booking ID
- Session ID reference
- Timestamps (created_at, updated_at)

#### **Doctor** (doctors/models.py)
- Personal info (name, email, phone, photo)
- Specialization relationship
- Qualifications and experience
- Consultation fee
- Active status
- Bio

#### **DoctorSchedule** (doctors/models.py)
- Doctor relationship
- Day of week (0-6)
- Start and end times
- Slot duration (configurable: 15, 30, 45, 60 minutes)
- Active toggle

#### **Specialization** (doctors/models.py)
- Name (unique)
- Description
- Keywords for AI matching (comma-separated)
- Example: "leg pain, bone, fracture, joint, back pain, arthritis"

#### **AppointmentHistory** (appointments/models.py)
- Tracks all changes to appointments
- Action type (status_change, reschedule, cancellation, creation, update)
- Changed by (patient, doctor, admin, system)
- Old and new dates/times for rescheduling
- Reason for change

#### **SMSNotification** (appointments/models.py)
- Appointment reference
- Type (confirmation, reminder, cancellation, reschedule)
- Message body
- Twilio message SID
- Delivery status (sent, delivered, failed, undelivered)
- Error messages

#### **PatientRecord** (patient_booking/models.py)
- Legacy/parallel table to Appointment
- Stores: booking_id, name, phone, email, doctor_name, department, date
- Separate from main Appointment model for compatibility

---

## 9. AI/LLM INTEGRATION

### Service: ClaudeService
**File:** `chatbot/claude_service.py` (246 lines)

**Current Model:** Google Generative AI (Gemini 2.5-flash)
- Using: `genai.GenerativeModel("gemini-2.5-flash")`
- API Key: From `settings.ANTHROPIC_API_KEY` (environment variable)

**Key Functions:**

1. **analyze_symptoms(symptoms_text)**
   - Input: Patient's symptom description
   - Output: Recommended specialization with confidence level
   - Process: 
     - Lists all available specializations
     - Asks Gemini to analyze and match
     - Returns JSON with specialization, confidence, reasoning
   - Fallback: Returns "General Physician" if no match

2. **detect_intent(message, stage, context)**
   - Detects user intent: proceed, change_doctor, change_date, change_time, go_back, clarify, cancel
   - Used for understanding corrections and changes
   - Looks for phrases like: "actually", "wait", "no", "change", "different", "instead"
   - Returns intent with confidence level

3. **extract_information(text, info_type)**
   - Extracts: name, phone, email, age from natural language
   - Intelligent parsing (handles various formats)
   - Returns: Extracted value or None if not found

4. **generate_conversational_response(message, context)**
   - Generates natural, friendly bot responses
   - Context-aware based on booking stage
   - Guidelines: Empathetic, concise, professional

5. **generate_contextual_response(message, intent, stage, context)**
   - Acknowledges user intent
   - Provides helpful guidance
   - Handles corrections and changes naturally

### Conversation Manager
**File:** `chatbot/conversation_manager.py` (1,384 lines)

**Core Logic:**
- Manages multi-stage conversation state
- Routes user messages to appropriate handlers
- Maintains conversation history
- Collects appointment data progressively
- Validates data at each stage

**State Persistence:**
- Uses Django cache (timeout: 1 hour)
- Session-based state storage
- Full conversation history with timestamps

---

## 10. KEY ENTRY POINTS & API ROUTES

### URL Routes
```
GET  /                          → home() - Landing page
GET  /chatbot/                  → chatbot_page() - Chat interface
POST /api/chatbot/              → ChatbotAPIView.post() - Chat API
GET  /api/chatbot/              → ChatbotAPIView.get() - API info
GET  /admin/                    → Django admin panel
GET  /admin-panel/              → Custom admin dashboard
GET  /whatsapp/...              → WhatsApp webhook/integration
```

### Main View Entry Points

**Patient Side:**
1. `patient_booking/views.py - home()` - Landing page
2. `patient_booking/views.py - chatbot_page()` - Chat interface HTML
3. `patient_booking/views.py - ChatbotAPIView.post()` - Chat API (REST)

**Admin Side:**
1. `admin_panel/views.py` - Dashboard
2. `admin_panel/views.py` - Calendar view

**Chatbot Logic:**
1. `chatbot/conversation_manager.py` - Main conversation orchestrator
2. `chatbot/claude_service.py` - AI integration
3. `chatbot/date_parser.py` - Date parsing utilities

---

## 11. IMPORTANT FILES FOR VOICE INTEGRATION

### Critical Files to Modify

1. **`templates/patient_booking/chatbot.html`** (382 lines)
   - Add microphone button to input area
   - Add speaker icon to bot messages
   - Integrate Web Audio API
   - Add audio controls

2. **`patient_booking/views.py`**
   - Add voice recording endpoint
   - Add audio file upload handling
   - Integrate speech-to-text API

3. **`chatbot/conversation_manager.py`**
   - Add voice command handling
   - Support audio message responses

4. **`config/settings.py`**
   - Add speech-to-text API keys (Google Cloud Speech, AWS Transcribe, etc.)
   - Add text-to-speech API keys (Google Cloud TTS, AWS Polly, etc.)
   - Configure audio processing settings

5. **`requirements.txt`**
   - Add audio libraries (SpeechRecognition, pydub, etc.)
   - Add TTS libraries (gTTS, pyttsx3, etc.)
   - Add WebRTC/audio processing libraries

### Files to Create

1. **`chatbot/voice_service.py`** - Speech-to-text and text-to-speech service
2. **`static/js/voice_handler.js`** - Client-side voice recording/playback
3. **`templates/patient_booking/voice_chatbot.html`** - Voice-enabled chat interface

---

## 12. CONFIGURATION & ENVIRONMENT VARIABLES

### Required Settings (.env)
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# API Keys
ANTHROPIC_API_KEY=your-gemini-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Speech Services (for voice implementation)
GOOGLE_CLOUD_SPEECH_CREDENTIALS=...
GOOGLE_CLOUD_TTS_CREDENTIALS=...
```

### Current API Keys in Settings
- `ANTHROPIC_API_KEY` - Using Gemini 2.5-flash model
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` - SMS service

---

## 13. DATA FLOW DIAGRAM

```
Web Browser
    ↓
[chatbot.html] - User types message
    ↓
JavaScript sends POST to /api/chatbot/
    ↓
ChatbotAPIView.post() (patient_booking/views.py)
    ↓
ConversationManager.process_message() (chatbot/conversation_manager.py)
    ↓
    ├─→ _handle_symptoms() → ClaudeService.analyze_symptoms()
    ├─→ _handle_doctor_selection() → Doctor.objects.filter()
    ├─→ _handle_date_selection() → DoctorSchedule.objects.filter()
    ├─→ _handle_time_selection() → Available slots calculation
    ├─→ _handle_patient_details() → ClaudeService.extract_information()
    └─→ _handle_confirmation() 
        ├─→ Appointment.objects.create()
        ├─→ PatientRecord.objects.create()
        ├─→ AppointmentHistory.objects.create()
        ├─→ TwilioSMSService.send_appointment_confirmation()
        └─→ SMS sent to patient phone
    ↓
JSON response sent back to browser
    ↓
JavaScript updates chat UI with response
```

---

## 14. SUMMARY & KEY INSIGHTS

### Strengths
✅ Clean separation of concerns (conversation logic, AI service, SMS)
✅ Intelligent intent detection with AI
✅ Phone number normalization for India
✅ Multi-stage conversation flow
✅ SMS integration for notifications
✅ Appointment history tracking
✅ Session-based state management
✅ WhatsApp integration ready

### Current Limitations
❌ No voice/audio functionality
❌ Frontend framework is vanilla JS (not React/Vue)
❌ Single booking flow (could support more variants)
❌ No authentication for chat (should add for production)
❌ No rate limiting on API
❌ Limited customization for specializations

### Opportunities for Voice Integration
1. **Speech-to-Text:** Replace text input with voice commands
2. **Text-to-Speech:** Read bot responses aloud
3. **Voice Confirmation:** Voice-based appointment confirmation
4. **Accessibility:** Better support for users with visual impairments
5. **Mobile-First:** Natural fit for mobile app

### Recommended Tech Stack for Voice
- **Frontend Speech-to-Text:** Web Speech API (free, browser-native) OR Google Cloud Speech-to-Text
- **Frontend Text-to-Speech:** Web Speech API (free) OR Google Cloud Text-to-Speech
- **Backend Speech Services:** Google Cloud Speech-to-Text API OR AWS Transcribe
- **Backend Text-to-Speech:** Google Cloud Text-to-Speech OR AWS Polly

---

## 15. FILE LOCATIONS (ABSOLUTE PATHS)

### Core Application Files
- `/home/user/claud-appoimnet/config/settings.py` - Django settings
- `/home/user/claud-appoimnet/config/urls.py` - URL routing
- `/home/user/claud-appoimnet/chatbot/conversation_manager.py` - Main booking logic
- `/home/user/claud-appoimnet/chatbot/claude_service.py` - AI integration
- `/home/user/claud-appoimnet/appointments/models.py` - Appointment model
- `/home/user/claud-appoimnet/doctors/models.py` - Doctor model
- `/home/user/claud-appoimnet/twilio_service.py` - SMS service
- `/home/user/claud-appoimnet/templates/patient_booking/chatbot.html` - Chat UI

### Key Models
- `/home/user/claud-appoimnet/appointments/models.py` - Appointment, AppointmentHistory, SMSNotification
- `/home/user/claud-appoimnet/doctors/models.py` - Doctor, Specialization, DoctorSchedule, DoctorLeave
- `/home/user/claud-appoimnet/patient_booking/models.py` - PatientRecord

### Views & URLs
- `/home/user/claud-appoimnet/patient_booking/views.py` - Chat views
- `/home/user/claud-appoimnet/patient_booking/urls.py` - Patient routes
- `/home/user/claud-appoimnet/admin_panel/views.py` - Admin dashboard
- `/home/user/claud-appoimnet/whatsapp_integration/views.py` - WhatsApp handler

### Configuration
- `/home/user/claud-appoimnet/.env.example` - Environment template
- `/home/user/claud-appoimnet/requirements.txt` - Python dependencies
- `/home/user/claud-appoimnet/README.md` - Documentation

---

**Report Generated:** 2025-11-10  
**Branch:** claude/add-voice-system-msg-011CUykwy7MGRn95xvE53DUk

