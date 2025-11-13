# Voice Intelligence Assistant

A sophisticated Voice Intelligence Assistant designed to handle appointment booking through natural voice conversations with advanced intent recognition, mixed-language support, and structured database interactions.

## Overview

This Voice Intelligence Assistant transforms your appointment booking system into a conversational AI that can:

✅ **Understand** voice inputs with error correction and mixed-language support
✅ **Identify** user intent with high accuracy using Gemini AI
✅ **Convert** speech to structured JSON actions for backend processing
✅ **Execute** database operations seamlessly
✅ **Generate** natural, conversational voice responses

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER VOICE INPUT                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Voice Intelligence Service                         │
│  • Speech correction & understanding                         │
│  • Mixed language support (EN/HI/TA/ML)                      │
│  • Entity extraction (names, dates, times, phones)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Intent Identification (Gemini AI)                  │
│  • appointment_booking                                       │
│  • appointment_lookup                                        │
│  • appointment_cancel/reschedule                             │
│  • doctor_query, general_query, support_request              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           JSON Action Generation                             │
│  {                                                           │
│    "action": "query_database",                               │
│    "query_type": "create_appointment",                       │
│    "parameters": {...}                                       │
│  }                                                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Database Action Handler                            │
│  • Executes database queries                                 │
│  • Returns structured results                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           Natural Language Response Generator                │
│  • Converts DB results to conversational speech              │
│  • Context-aware responses                                   │
│  • Follow-up questions                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    VOICE OUTPUT TO USER                      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. **voice_intelligence_service.py**
Core service that handles:
- Voice understanding with error correction
- Mixed language support (English, Hindi, Tamil, Malayalam)
- Intent identification using Gemini AI
- JSON action generation
- Natural language response generation

### 2. **database_action_handler.py**
Database operations handler:
- Executes structured JSON actions
- Manages appointments (create, lookup, cancel, reschedule)
- Doctor searches and availability checks
- Returns formatted results

### 3. **voice_intelligence_manager.py**
Orchestration layer:
- Manages complete conversation flow
- Session management with context tracking
- Coordinates between services
- Handles missing information detection

### 4. **voice_intelligence_views.py**
REST API endpoints:
- `/api/intelligence/` - Main voice processing endpoint
- `/api/database-action/` - Direct database action execution
- `/api/intent-analysis/` - Intent analysis (testing/debugging)
- `/api/session/` - Session management
- `/api/v2/` - Legacy-compatible endpoint

## Installation & Setup

### 1. Dependencies
Ensure these are in your `requirements.txt`:
```
google-generativeai>=0.3.0
Django>=4.2.0
```

### 2. Configuration
Add to your Django `settings.py`:
```python
# Gemini AI API Key (used for voice intelligence)
ANTHROPIC_API_KEY = 'your-gemini-api-key-here'

# Cache backend for session management
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'voice-intelligence-cache',
    }
}
```

### 3. URL Configuration
The URLs are already configured in `/voicebot/urls.py`.

Include in your main `urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('voicebot/', include('voicebot.urls')),
]
```

## Usage

### Quick Start Example

```python
from voicebot.voice_intelligence_manager import VoiceIntelligenceManager

# Initialize manager
manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

# Process voice input
result = manager.process_voice_input(
    "Book appointment tomorrow 10 AM with Dr. Rahul",
    session_id=None  # Will create new session
)

# Get the voice response
voice_response = result['voice_response']
# "Excellent news! Your appointment with Dr. Rahul is confirmed..."

# Get session ID for continuity
session_id = result['session_id']
```

### API Usage

#### Full Voice Processing
```bash
curl -X POST http://localhost:8000/voicebot/api/intelligence/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "I want to book appointment tomorrow with Dr. Rahul",
    "session_id": "optional-session-id"
  }'
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "voice_response": "Natural language response...",
  "action": "database_query_completed",
  "data": {
    "intent": {...},
    "database_action": {...},
    "database_result": {...}
  }
}
```

#### Direct Database Action
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

#### Intent Analysis (Testing)
```bash
curl -X POST http://localhost:8000/voicebot/api/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "Check my appointment"
  }'
```

## Supported Intents

| Intent | Description | Example |
|--------|-------------|---------|
| `appointment_booking` | Create new appointment | "Book appointment tomorrow with Dr. Rahul" |
| `appointment_lookup` | Check existing appointments | "Check my appointment with phone 9876543210" |
| `appointment_cancel` | Cancel appointment | "Cancel my appointment" |
| `appointment_reschedule` | Reschedule appointment | "Reschedule to next Monday 2 PM" |
| `doctor_query` | Ask about doctors | "Do you have a cardiologist?" |
| `general_query` | General questions | "What are your clinic hours?" |
| `support_request` | Help/clarification | "I need help booking an appointment" |

## Database Query Types

| Query Type | Action | Required Parameters |
|------------|--------|---------------------|
| `create_appointment` | Book new appointment | patient_name, phone, doctor_id/doctor_name, date, time |
| `appointment_lookup` | Find appointments | phone OR appointment_id |
| `cancel_appointment` | Cancel appointment | appointment_id, phone |
| `reschedule_appointment` | Reschedule | appointment_id, phone, new_date, new_time |
| `get_doctors` | List doctors | doctor_name OR specialization (optional) |
| `get_doctor_by_symptoms` | Recommend by symptoms | symptoms (list) |
| `check_availability` | Check available slots | doctor_id/doctor_name, date |

## Features

### 🌐 Multi-Language Support
- **English** (Standard and Indian-style)
- **Hindi** mixed speech
- **Malayalam** mixed speech
- **Tamil** mixed speech

Example:
```
Input: "Kal morning Doctor Rahul se milna hai"
Corrected: "I want to meet Doctor Rahul tomorrow morning"
```

### 🔧 Speech Error Correction
- Corrects spelling mistakes
- Handles incomplete speech
- Processes unclear audio
- Extracts meaning from fragmented input

Example:
```
Input: "um... book... doctor... nine eight seven... tomorrow?"
Understood: "Book doctor appointment tomorrow, phone: 987..."
```

### 🧠 Entity Extraction
Automatically extracts:
- **Names** (patient names, doctor names)
- **Phone numbers** (10-digit, various formats)
- **Dates** (relative, specific, natural language)
- **Times** (12/24 hour, natural language)
- **Symptoms** (for doctor recommendation)

### 💬 Natural Conversation
- Context-aware responses
- Follow-up questions
- Clarification requests
- Friendly, professional tone

### 📊 Session Management
- Conversation continuity
- Context tracking
- Information persistence
- Multi-turn conversations

## Example Conversations

### Example 1: Complete Booking Flow

```
User: "Hello, I want to book an appointment"
Bot: "Welcome to MedCare Clinic! I'd be happy to help you book an appointment.
      May I have your name, please?"

User: "My name is John Doe"
Bot: "Nice to meet you, John! Which doctor would you like to see?"

User: "I have fever and headache"
Bot: "I understand. Based on your symptoms, I recommend Dr. Rahul Kumar,
      our General Physician. Would you like to book with Dr. Rahul?"

User: "Yes, tomorrow morning"
Bot: "What time works best for you tomorrow morning?"

User: "10 AM"
Bot: "Perfect! And what's the best phone number to reach you?"

User: "9876543210"
Bot: "Excellent news, John! Your appointment with Dr. Rahul Kumar is confirmed
      for tomorrow at 10:00 AM. Your booking ID is APT000123.
      You'll receive a confirmation message shortly. Is there anything else I can help with?"
```

### Example 2: Quick Lookup

```
User: "Check my appointment, phone 9876543210"
Bot: "I found your appointment with Dr. Rahul Kumar on tomorrow at 10:00 AM.
      The status is confirmed. Would you like to reschedule or cancel this appointment?"
```

### Example 3: Mixed Language

```
User: "Nale morning Doctor Rahul inte appointment book cheyyanam"
Bot: "I understand you want to book an appointment with Doctor Rahul tomorrow morning.
      What time would you prefer?"
```

## Testing

### Run Test Script
```bash
cd /home/user/claud-appoimnet/voicebot
python test_voice_intelligence.py
```

This will run through various test scenarios and show you:
- Voice understanding results
- Intent identification
- JSON actions generated
- Missing information detection

### Manual Testing
```bash
# Start Django shell
python manage.py shell

# Import manager
from voicebot.voice_intelligence_manager import VoiceIntelligenceManager

# Create manager
manager = VoiceIntelligenceManager()

# Test a scenario
result = manager.process_voice_input("Book appointment tomorrow with Dr. Rahul")
print(result['voice_response'])
```

## File Structure

```
voicebot/
├── voice_intelligence_service.py      # Core AI service
├── database_action_handler.py         # Database operations
├── voice_intelligence_manager.py      # Orchestration layer
├── voice_intelligence_views.py        # REST API endpoints
├── urls.py                            # URL routing (updated)
├── test_voice_intelligence.py         # Test script
├── README_VOICE_INTELLIGENCE.md       # This file
└── VOICE_INTELLIGENCE_EXAMPLES.md     # Detailed examples
```

## API Reference

See `VOICE_INTELLIGENCE_EXAMPLES.md` for detailed API documentation and examples.

## Customization

### Change Clinic Name
```python
manager = VoiceIntelligenceManager(clinic_name="Your Clinic Name")
```

### Customize Responses
Edit methods in `voice_intelligence_service.py`:
- `_format_appointment_confirmation()`
- `_format_appointment_details()`
- `_format_doctor_list()`
- `_generate_error_response()`

### Add New Intents
1. Add intent to `identify_intent()` method
2. Add query type mapping in `generate_database_action()`
3. Implement database handler in `database_action_handler.py`
4. Add response format in `generate_voice_response()`

### Adjust AI Model
Change model in `voice_intelligence_service.py`:
```python
self.model = genai.GenerativeModel('gemini-2.0-flash-exp')  # or other model
```

## Troubleshooting

### Issue: "Invalid API Key"
**Solution:** Set `ANTHROPIC_API_KEY` in Django settings with valid Gemini API key.

### Issue: Sessions not persisting
**Solution:** Configure Django cache properly in settings.py.

### Issue: Low accuracy in voice understanding
**Solution:** Ensure voice input is clear. Adjust confidence thresholds in the service.

### Issue: Database operations failing
**Solution:** Check database models are properly set up (Doctor, Appointment, DoctorSchedule).

## Performance Considerations

- **Session Storage**: Uses Django cache (in-memory). For production, use Redis.
- **AI Calls**: Each voice input makes 1-2 Gemini AI calls. Consider rate limiting.
- **Database Queries**: Optimized with select_related() and proper indexing.

## Security

- ✅ CSRF protection on all POST endpoints
- ✅ Phone number validation
- ✅ Session isolation
- ✅ SQL injection prevention (Django ORM)
- ⚠️ Add authentication for production use
- ⚠️ Add rate limiting for API endpoints

## Production Checklist

- [ ] Set up Redis for session storage
- [ ] Add authentication to API endpoints
- [ ] Implement rate limiting
- [ ] Set up proper logging
- [ ] Configure HTTPS
- [ ] Add API key rotation
- [ ] Set up monitoring and alerts
- [ ] Add user consent for voice recording (if applicable)
- [ ] Implement data privacy measures (GDPR/HIPAA compliance)

## License

This is part of the MedCare Clinic appointment booking system.

## Support

For issues or questions:
1. Check `VOICE_INTELLIGENCE_EXAMPLES.md` for detailed examples
2. Run `test_voice_intelligence.py` to verify setup
3. Check Django logs for error details

---

**Built with:**
- Django 4.2+
- Google Gemini AI (gemini-2.0-flash-exp)
- Python 3.8+

**Version:** 1.0.0
**Last Updated:** November 2025
