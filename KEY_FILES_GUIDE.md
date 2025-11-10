# Medical Appointment System - Key Files Guide

## 📑 Quick File Reference

### 🎯 Most Important Files for Understanding the System

#### 1. **Booking Flow & Conversation Logic**
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/claud-appoimnet/chatbot/conversation_manager.py` | 1,384 | Core conversation orchestrator, all 7 booking stages |
| `/home/user/claud-appoimnet/chatbot/claude_service.py` | 246 | AI service (Gemini 2.5-flash), symptom analysis, intent detection |
| `/home/user/claud-appoimnet/patient_booking/views.py` | ~64 | API endpoint handler, entry point for chat messages |

#### 2. **Database Models**
| File | Purpose |
|------|---------|
| `/home/user/claud-appoimnet/appointments/models.py` | Appointment, AppointmentHistory, SMSNotification |
| `/home/user/claud-appoimnet/doctors/models.py` | Doctor, Specialization, DoctorSchedule, DoctorLeave |
| `/home/user/claud-appoimnet/patient_booking/models.py` | PatientRecord (legacy/parallel model) |

#### 3. **User Interface (Frontend)**
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/claud-appoimnet/templates/patient_booking/chatbot.html` | 382 | Main chat interface (vanilla JS) |
| `/home/user/claud-appoimnet/templates/patient_booking/home.html` | 200 | Landing page with CTA |

#### 4. **Configuration & Setup**
| File | Purpose |
|------|---------|
| `/home/user/claud-appoimnet/config/settings.py` | Django configuration, API keys, database |
| `/home/user/claud-appoimnet/config/urls.py` | URL routing setup |
| `/home/user/claud-appoimnet/requirements.txt` | Python dependencies |
| `/home/user/claud-appoimnet/.env.example` | Environment variables template |

#### 5. **Communication Services**
| File | Lines | Purpose |
|------|-------|---------|
| `/home/user/claud-appoimnet/twilio_service.py` | 308 | SMS notifications (Twilio integration) |
| `/home/user/claud-appoimnet/whatsapp_integration/whatsapp_service.py` | 11,110 | WhatsApp messaging |

#### 6. **Admin & Dashboard**
| File | Purpose |
|------|---------|
| `/home/user/claud-appoimnet/admin_panel/views.py` | Admin dashboard and calendar view |
| `/home/user/claud-appoimnet/admin_panel/urls.py` | Admin panel routes |

---

## 📂 Complete File Structure

```
/home/user/claud-appoimnet/
│
├── 🎯 ROOT CONFIGURATION
│   ├── manage.py                              Django management script
│   ├── requirements.txt                       Python dependencies (10 packages)
│   ├── .env.example                          Environment variables template
│   ├── README.md                             Project documentation
│   ├── CODEBASE_EXPLORATION.md               (Generated) Full codebase analysis
│   ├── BOOKING_FLOW_DIAGRAM.md               (Generated) Visual flow diagrams
│   └── KEY_FILES_GUIDE.md                    (This file)
│
├── 📋 MAIN DJANGO CONFIG
│   └── config/
│       ├── __init__.py
│       ├── asgi.py                           ASGI config for async
│       ├── settings.py                       ⭐ Main Django settings (API keys, DB, apps)
│       ├── urls.py                           ⭐ URL routing (routes to all apps)
│       └── wsgi.py                           WSGI config for deployment
│
├── 👨‍⚕️ DOCTORS APP
│   └── doctors/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── admin.py                          Django admin customization
│       ├── models.py                         ⭐ Doctor, Specialization, DoctorSchedule, DoctorLeave
│       ├── views.py                          Doctor views
│       ├── migrations/                       Database migrations
│       └── tests.py                          Unit tests
│
├── 📅 APPOINTMENTS APP
│   └── appointments/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── admin.py                          Django admin customization
│       ├── models.py                         ⭐ Appointment, AppointmentHistory, SMSNotification
│       ├── views.py                          Appointment views
│       ├── migrations/                       Database migrations
│       └── tests.py                          Unit tests
│
├── 🤖 CHATBOT APP (CORE LOGIC)
│   └── chatbot/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── admin.py                          Django admin customization
│       ├── models.py                         Chatbot models (empty)
│       ├── views.py                          Chatbot views
│       ├── conversation_manager.py           ⭐⭐⭐ Core conversation flow (1,384 lines)
│       ├── claude_service.py                 ⭐⭐ AI service (Gemini integration)
│       ├── date_parser.py                    Utility for date parsing
│       ├── tests.py                          Unit tests
│       └── migrations/                       Database migrations
│
├── 🛒 PATIENT BOOKING APP
│   └── patient_booking/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── models.py                         ⭐ PatientRecord model
│       ├── views.py                          ⭐ ChatbotAPIView entry point
│       ├── urls.py                           ⭐ Routes (/, /chatbot/, /api/chatbot/)
│       ├── tests.py                          Unit tests
│       └── migrations/                       Database migrations
│
├── 🏢 ADMIN PANEL APP
│   └── admin_panel/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── admin.py                          Custom admin configuration
│       ├── models.py                         Admin panel models
│       ├── views.py                          ⭐ Dashboard and calendar views
│       ├── urls.py                           ⭐ Admin panel routes
│       ├── tests.py                          Unit tests
│       ├── migrations/                       Database migrations
│       └── templates/admin_panel/
│           └── calendar.html                 Calendar view template
│
├── 💬 WHATSAPP INTEGRATION
│   └── whatsapp_integration/
│       ├── __init__.py
│       ├── apps.py                           App configuration
│       ├── admin.py                          Django admin customization
│       ├── models.py                         WhatsApp models
│       ├── views.py                          ⭐ WhatsApp webhook handler
│       ├── urls.py                           WhatsApp routes
│       ├── whatsapp_service.py              ⭐ WhatsApp service (11,110 lines!)
│       ├── tests.py                          Unit tests
│       ├── migrations/                       Database migrations
│       └── templates/whatsapp_integration/
│           └── whatsapp_chat.html            WhatsApp chat template
│
├── 📱 FRONTEND TEMPLATES
│   └── templates/
│       ├── patient_booking/
│       │   ├── home.html                     ⭐ Landing page (200 lines)
│       │   └── chatbot.html                  ⭐ Chat interface (382 lines)
│       └── admin_panel/
│           └── calendar.html                 Calendar view
│
├── 📞 SMS/COMMUNICATION SERVICE
│   └── twilio_service.py                     ⭐ Twilio SMS service (308 lines)
│       └── Functions:
│           ├── send_sms()
│           ├── send_appointment_confirmation()
│           ├── send_cancellation_notification()
│           ├── send_reschedule_notification()
│           └── _normalize_phone_number()    (Handles +91 for India)
│
├── 📁 STATIC FILES (Not present yet, would go here)
│   └── static/
│       ├── css/                              CSS stylesheets
│       ├── js/                               JavaScript files
│       └── images/                           Images and assets
│
├── 📁 MEDIA FILES
│   └── media/
│       └── doctors/                          Doctor profile images
│
└── 🗄️ DATABASE
    └── db.sqlite3                            SQLite database (created after migrations)
```

---

## 🔗 Dependency Map

### Core Booking Flow Dependencies

```
ChatbotAPIView
    ↓
ConversationManager
    ├─→ ClaudeService (AI analysis)
    ├─→ Doctor model (DB queries)
    ├─→ DoctorSchedule model
    ├─→ Appointment model (create appointment)
    ├─→ AppointmentHistory model (audit trail)
    ├─→ PatientRecord model (legacy)
    ├─→ Specialization model
    └─→ TwilioService (SMS)
        └─→ SMSNotification model (logging)
```

### Import Dependencies

```
patient_booking/views.py
    └─ from chatbot.conversation_manager import ConversationManager
       └─ from chatbot.claude_service import ClaudeService
          └─ from doctors.models import Specialization, Doctor
          └─ import google.generativeai as genai
       └─ from doctors.models import Doctor, DoctorSchedule
       └─ from appointments.models import Appointment
       └─ from patient_booking.models import PatientRecord
       └─ from twilio_service import get_twilio_service
          └─ from twilio.rest import Client
          └─ from appointments.models import SMSNotification
```

---

## 🚀 Entry Points & API Endpoints

### Frontend Entry Points
| URL | Handler | File |
|-----|---------|------|
| `/` | home() | patient_booking/views.py |
| `/chatbot/` | chatbot_page() | patient_booking/views.py |

### API Entry Points
| Method | URL | Handler | File |
|--------|-----|---------|------|
| POST | `/api/chatbot/` | ChatbotAPIView.post() | patient_booking/views.py |
| GET | `/api/chatbot/` | ChatbotAPIView.get() | patient_booking/views.py |

### Admin Entry Points
| URL | Purpose | File |
|-----|---------|------|
| `/admin/` | Django default admin | config/admin.py |
| `/admin-panel/` | Custom admin dashboard | admin_panel/urls.py |
| `/whatsapp/` | WhatsApp webhook | whatsapp_integration/urls.py |

---

## 🔑 Key Data Models Summary

### Specialization
```
Fields: id, name, description, keywords, created_at
Purpose: Medical specializations for symptom matching
Example: "Orthopedic" with keywords "leg pain, bone, fracture, joint"
```

### Doctor
```
Fields: id, user, name, specialization, phone, email, qualification, 
        experience_years, consultation_fee, is_active, photo, bio
Purpose: Doctor profile with schedule
Relationships: FK to Specialization, O2O to User, FK in DoctorSchedule
```

### DoctorSchedule
```
Fields: id, doctor, day_of_week, start_time, end_time, slot_duration, is_active
Purpose: Weekly working hours and slot availability
Example: Monday 9 AM - 5 PM with 30-minute slots
```

### Appointment
```
Fields: id, doctor, patient_name, patient_phone, patient_email, patient_age, 
        patient_gender, appointment_date, appointment_time, symptoms, notes, 
        status, booking_id, session_id, created_at, updated_at
Purpose: Book appointment with doctor
Statuses: pending, confirmed, cancelled, completed, no_show
```

### AppointmentHistory
```
Fields: id, appointment, status, notes, changed_by, changed_at, action, 
        old_date, old_time, new_date, new_time, reason
Purpose: Audit trail for appointment changes
Actions: status_change, reschedule, cancellation, creation, update
```

### SMSNotification
```
Fields: id, appointment, notification_type, phone_number, message_body, 
        message_sid, status, error_message, sent_at, updated_at
Purpose: Track SMS delivery
Types: confirmation, reminder, cancellation, reschedule
Status: sent, delivered, failed, undelivered
```

### PatientRecord
```
Fields: id, booking_id, name, phone_number, mail_id, doctor_name, 
        department, appointment_date, created_at, updated_at
Purpose: Legacy/parallel appointment tracking
Note: Separate from main Appointment model for compatibility
```

---

## 🎨 Frontend Technologies

### Chat Interface (chatbot.html)
- **HTML:** Standard semantic HTML
- **CSS:** Inline styles (no external CSS file)
  - Gradient backgrounds: blue (#2563eb) to purple (#7c3aed)
  - Animations: Fade-in, typing indicator dots
  - Responsive design: Mobile-friendly
  
- **JavaScript:** Vanilla JS (no frameworks)
  - Functions:
    - generateSessionId() - Create unique session
    - addMessage() - Add message to chat
    - displayOptions() - Show clickable buttons
    - selectOption() - Handle button clicks
    - sendMessage() - POST to /api/chatbot/
  - No external JS libraries

### Key CSS Classes
```
.chat-wrapper              Main container
.chat-header              Header with title
.messages                 Message scroll area
.message                  Individual message
.bot-message              Bot message styling (gray)
.user-message             User message styling (blue)
.typing-indicator         Typing dots animation
.options-container        Quick action buttons
.option-btn               Individual button styling
.input-area               Input and send button
#user-input               Text input field
#send-btn                 Send button
```

---

## 🔐 Security & Configuration

### API Keys (from .env)
```
ANTHROPIC_API_KEY           Gemini API key (currently in use)
TWILIO_ACCOUNT_SID          Twilio SMS account
TWILIO_AUTH_TOKEN           Twilio authentication
TWILIO_PHONE_NUMBER         SMS sending phone number
SECRET_KEY                  Django secret key
DEBUG                       Debug mode (True for dev, False for prod)
ALLOWED_HOSTS               Allowed domain names
```

### Current Issues
- ❌ API key embedded in settings.py (SECURITY: Should use env variable)
- ❌ No CSRF protection on /api/chatbot/ (csrf_exempt decorator)
- ❌ No rate limiting on chat API
- ❌ No authentication for patient chat

---

## 📊 Code Statistics

| Component | Lines | Status |
|-----------|-------|--------|
| conversation_manager.py | 1,384 | ✅ Complete |
| whatsapp_service.py | 11,110 | ✅ Complete |
| twilio_service.py | 308 | ✅ Complete |
| chatbot.html | 382 | ✅ Complete |
| claude_service.py | 246 | ✅ Complete |
| **Total Backend Python** | ~2,000+ | ✅ Ready |
| **Total Frontend JS** | ~100 lines | ✅ Functional |
| **Total Templates** | ~582 | ✅ Complete |

---

## ⚙️ Technology Versions

| Technology | Version | Purpose |
|-----------|---------|---------|
| Django | 4.2.7 | Web framework |
| Python | 3.8+ | Programming language |
| SQLite | 3 | Development database |
| Twilio | 8.10.0 | SMS service |
| google-generativeai | 0.3.2 | Gemini AI API |
| djangorestframework | 3.14.0 | REST API |
| django-cors-headers | 4.3.1 | CORS support |

---

## 🚀 Next Steps for Voice Integration

### Phase 1: Frontend Setup
1. Modify `templates/patient_booking/chatbot.html`
   - Add mic button for speech-to-text
   - Add speaker icon for text-to-speech
   - Integrate Web Audio API or Web Speech API

2. Create `static/js/voice_handler.js`
   - Speech-to-text functionality
   - Audio playback functionality
   - Error handling for browser compatibility

### Phase 2: Backend Setup
1. Create `chatbot/voice_service.py`
   - Speech-to-text API integration (Google Cloud Speech or AWS Transcribe)
   - Text-to-speech API integration (Google Cloud TTS or AWS Polly)

2. Update `patient_booking/views.py`
   - Add audio upload endpoint
   - Add voice message handling

3. Update `config/settings.py`
   - Add speech service API keys
   - Add audio processing configuration

### Phase 3: Integration
1. Update `chatbot/conversation_manager.py`
   - Handle voice message input
   - Trigger audio responses

2. Update `requirements.txt`
   - Add audio libraries (SpeechRecognition, pydub, etc.)

---

## 📝 File Naming Conventions

**Current Files:**
- `models.py` - Django models
- `views.py` - View handlers
- `urls.py` - URL routing
- `admin.py` - Admin customization
- `services.py` - Service classes (e.g., `claude_service.py`, `twilio_service.py`)
- `_manager.py` - Manager/orchestrator (e.g., `conversation_manager.py`)
- `_handler.js` - JavaScript handlers (to be created)

---

## 🎯 How to Find Specific Functionality

| Need | File |
|------|------|
| Add new doctor specialization | `doctors/models.py` + `doctors/admin.py` |
| Change appointment duration | `doctors/models.py` - DoctorSchedule.slot_duration |
| Modify SMS message | `twilio_service.py` - _format_confirmation_message() |
| Change chat UI colors | `templates/patient_booking/chatbot.html` - CSS section |
| Add new booking stage | `chatbot/conversation_manager.py` - STAGES list + add handler |
| Change AI model | `chatbot/claude_service.py` - self.model assignment |
| Add new intent | `chatbot/claude_service.py` - detect_intent() |
| Modify conversation flow | `chatbot/conversation_manager.py` - process_message() |
| Add new doctor field | `doctors/models.py` - Doctor model |
| Change phone validation | `twilio_service.py` - _normalize_phone_number() |

---

**Generated:** 2025-11-10  
**Last Updated:** 2025-11-10  
**Status:** Ready for reference and voice system integration
