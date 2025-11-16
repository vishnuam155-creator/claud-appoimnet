# VoiceBot RAG System - Complete Documentation

## Overview

The VoiceBot module has been completely restructured to use an advanced **RAG (Retrieval-Augmented Generation)** system powered by **Gemini 2.5 Flash**. This system provides natural, conversational appointment booking with full context awareness, acting like a senior medical receptionist.

## 🎯 Key Features

### 1. **Full Conversation History**
- Persistent storage of all conversation messages
- Complete context awareness across the entire conversation
- Ability to reference previous parts of the conversation
- Session-based state management with database persistence

### 2. **Retrieval-Augmented Generation (RAG)**
- Real-time database context retrieval
- Fetches relevant information about:
  - Available doctors and their specializations
  - Real-time appointment slot availability
  - Doctor schedules and leave information
  - Patient booking history
  - Specialization keywords for symptom matching

### 3. **Natural Language Understanding**
- Understands complex, natural speech patterns
- Handles topic changes mid-conversation
- Detects and handles change requests at any stage
- Intelligent intent detection (proceed, change, cancel, clarify)
- Symptom-based doctor recommendation

### 4. **Dynamic Change Handling**
- **Change doctor** at any time during booking
- **Change date** even after selecting time
- **Change time slot** without restarting
- **Update phone number or name** at confirmation stage
- Seamless handling without making users feel they made a mistake

### 5. **Intelligent Slot Management**
- Real-time availability checking
- Proactive alternative suggestions when slots unavailable
- Next available date finder (up to 90 days)
- Alternative doctor suggestions from same specialization
- Context-aware slot recommendations

### 6. **Senior Receptionist Behavior**
- Warm, empathetic, and professional tone
- Proactive suggestions and helpful guidance
- Handles errors and unclear inputs gracefully
- Answers booking-related questions naturally
- Confirms critical information before finalizing

## 🏗️ Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     VoiceBot RAG System                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  views_rag.py    │───▶│  Voice Assistant │              │
│  │  (API Endpoint)  │    │  Manager RAG     │              │
│  └──────────────────┘    └─────────┬────────┘              │
│                                     │                        │
│           ┌─────────────────────────┼────────────────┐      │
│           │                         │                │      │
│           ▼                         ▼                ▼      │
│  ┌────────────────┐     ┌────────────────┐  ┌────────────┐│
│  │ Conversation   │     │  RAG Retriever │  │   Gemini   ││
│  │ Context Manager│     │   (Database)   │  │ RAG Service││
│  └────────────────┘     └────────────────┘  └────────────┘│
│           │                     │                  │        │
│           ▼                     ▼                  ▼        │
│  ┌────────────────┐     ┌────────────────┐  ┌────────────┐│
│  │ Voice          │     │ Doctor, Appt,  │  │  Gemini    ││
│  │ Conversation   │     │ Schedule Models│  │ 2.5 Flash  ││
│  │ Models         │     │                │  │    API     ││
│  └────────────────┘     └────────────────┘  └────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. **VoiceAssistantManagerRAG** (`voice_assistant_manager_rag.py`)
Main orchestrator that:
- Processes incoming voice messages
- Coordinates between all components
- Manages conversation flow
- Handles special intents (cancel, change requests)
- Creates final appointments

#### 2. **ConversationContextManager** (`conversation_context_manager.py`)
Manages conversation state:
- Loads/creates conversation sessions
- Stores message history
- Updates booking state
- Tracks conversation stage
- Provides session data access

#### 3. **RAGRetriever** (`rag_retriever.py`)
Database context retrieval:
- Fetches all available doctors
- Retrieves specializations with keywords
- Gets doctor availability summaries
- Checks real-time slot availability
- Finds alternative doctors
- Searches doctors by symptoms

#### 4. **GeminiRAGService** (`gemini_rag_service.py`)
LLM interaction layer:
- Generates responses with full context
- Builds comprehensive prompts
- Analyzes user intent
- Extracts structured data from responses
- Handles natural language understanding

#### 5. **Database Models** (`models.py`)
Persistent storage:
- **VoiceConversation**: Session and booking state
- **ConversationMessage**: Individual conversation messages

## 📋 API Endpoints

### Main RAG Endpoint

**Endpoint:** `POST /voicebot/api/`
**Content-Type:** `application/json` or `multipart/form-data`

#### Request Format

```json
{
  "message": "I want to book an appointment",
  "session_id": "voice_abc123" // Optional, auto-generated if not provided
}
```

#### Response Format

```json
{
  "success": true,
  "session_id": "voice_abc123",
  "message": "Hello! Welcome to MedCare Clinic...",
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

### Alternative Endpoints

- **`POST /voicebot/api/rag/`** - Same as main endpoint
- **`POST /voicebot/api/legacy/`** - Original implementation (backwards compatibility)
- **`GET /voicebot/api/`** - API documentation and information

## 🚀 Usage Examples

### Example 1: Simple Booking Flow

```python
# 1. Start conversation
POST /voicebot/api/
{
  "message": ""
}

Response: "Hello! Welcome to MedCare Clinic. May I have your name?"

# 2. Provide name
POST /voicebot/api/
{
  "message": "My name is John",
  "session_id": "voice_abc123"
}

Response: "Nice to meet you, John! How can I help you today?"

# 3. Describe symptoms
POST /voicebot/api/
{
  "message": "I have a severe headache",
  "session_id": "voice_abc123"
}

Response: "Based on your symptoms, I recommend Dr. Smith, our Neurologist..."

# 4. Continue the flow...
```

### Example 2: Changing Doctor Mid-Conversation

```python
# After selecting Dr. Smith and picking a date...

POST /voicebot/api/
{
  "message": "Actually, I want to see a different doctor",
  "session_id": "voice_abc123"
}

Response: "No problem! Which doctor would you like to book with instead?"

# System automatically:
# - Clears current doctor selection
# - Returns to doctor selection stage
# - Maintains all other collected information (name, date, etc.)
```

### Example 3: Handling Unavailable Slots

```python
POST /voicebot/api/
{
  "message": "I want an appointment tomorrow",
  "session_id": "voice_abc123"
}

Response: "I'm sorry, Dr. Smith doesn't have any available slots tomorrow.
However, I found availability on December 18th, which is in 2 days.
Would you like to book for that date instead?"

# System automatically:
# - Checks slot availability
# - Finds next available date
# - Suggests alternatives
# - Handles user's choice naturally
```

## 🛠️ Installation & Setup

### 1. Install Dependencies

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Gemini API Key

Update your `.env` file or Django settings:

```python
# In settings.py or .env
ANTHROPIC_API_KEY = "your_gemini_api_key_here"
```

**Note:** Despite the variable name `ANTHROPIC_API_KEY`, the system uses Google Gemini 2.5 Flash.

### 3. Run Migrations

```bash
python manage.py makemigrations voicebot
python manage.py migrate voicebot
```

### 4. Test the System

```bash
# Start Django server
python manage.py runserver

# Test API
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

## 📊 Database Schema

### VoiceConversation Model

| Field | Type | Description |
|-------|------|-------------|
| session_id | CharField | Unique session identifier |
| stage | CharField | Current conversation stage |
| patient_name | CharField | Patient's name |
| patient_phone | CharField | Patient's phone number |
| doctor_id | IntegerField | Selected doctor ID |
| doctor_name | CharField | Selected doctor name |
| appointment_date | DateField | Selected appointment date |
| appointment_time | TimeField | Selected time slot |
| appointment_id | IntegerField | Created appointment ID |
| completed | BooleanField | Booking completion status |
| created_at | DateTimeField | Session creation time |
| updated_at | DateTimeField | Last update time |

### ConversationMessage Model

| Field | Type | Description |
|-------|------|-------------|
| conversation | ForeignKey | Link to VoiceConversation |
| role | CharField | 'user', 'assistant', or 'system' |
| content | TextField | Message content |
| intent | CharField | Detected intent (optional) |
| extracted_data | JSONField | Extracted structured data |
| timestamp | DateTimeField | Message timestamp |

## 🎭 Conversation Stages

1. **greeting** - Initial welcome
2. **patient_name** - Collect patient name
3. **doctor_selection** - Select doctor (by name or symptoms)
4. **date_selection** - Choose appointment date
5. **time_selection** - Select time slot
6. **phone_collection** - Collect contact number
7. **confirmation** - Final confirmation
8. **completed** - Booking successfully completed

**Note:** Stages are flexible - the system can handle changes at any point!

## 🧠 Intent Detection

The system intelligently detects user intents:

- **proceed** - Normal flow, providing requested information
- **change_doctor** - Wants to change/select different doctor
- **change_date** - Wants to change appointment date
- **change_time** - Wants to change time slot
- **change_phone** - Wants to update phone number
- **change_name** - Wants to update name
- **cancel** - Wants to cancel booking
- **clarify** - Asking question or needs clarification
- **confirm** - Confirming booking details

## 🔧 Customization

### Modify System Prompts

Edit `voicebot/gemini_rag_service.py`:

```python
def _build_system_prompt(self):
    return """You are MediBot, a senior medical receptionist...

    YOUR ROLE AND PERSONALITY:
    - Customize personality here
    - Add specific clinic policies
    - Modify conversation style
    """
```

### Adjust RAG Context

Edit `voicebot/rag_retriever.py`:

```python
def get_all_context_for_conversation(self, session_data):
    # Add more context as needed
    context = {
        'doctors': self.get_all_doctors_context(),
        'specializations': self.get_specializations_context(),
        # Add custom context here
    }
    return context
```

### Change Conversation Behavior

Edit `voicebot/voice_assistant_manager_rag.py`:

```python
def _handle_special_intent(self, intent, extracted_data, booking_state, context):
    # Add custom intent handlers
    if intent == 'custom_intent':
        return self._handle_custom_intent(extracted_data)
```

## 📈 Admin Interface

Access the Django admin panel to view:

- **Voice Conversations**: See all booking sessions
  - Filter by stage, completion status
  - Search by patient name, phone, session ID
  - View booking details

- **Conversation Messages**: View message history
  - Filter by role (user/assistant/system)
  - Search by content
  - See extracted data and intents

## 🐛 Troubleshooting

### Issue: "Couldn't import Django"

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Verify Django is installed
pip list | grep Django
```

### Issue: Gemini API errors

**Solution:**
1. Check API key in settings
2. Verify API key has correct permissions
3. Check rate limits

### Issue: Database errors

**Solution:**
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Check database connection
python manage.py dbshell
```

### Issue: Conversations not persisting

**Solution:**
1. Verify migrations ran successfully
2. Check database connection
3. Ensure session_id is being passed in requests

## 🚨 Important Notes

1. **Session Management**: Always pass `session_id` in subsequent requests to maintain conversation context

2. **API Key**: The variable is named `ANTHROPIC_API_KEY` but contains Google Gemini API key (legacy naming)

3. **Backwards Compatibility**: Legacy endpoint available at `/voicebot/api/legacy/`

4. **Message Limit**: Conversation history limited to last 20 messages for performance

5. **Slot Caching**: Real-time slot checking - no caching for accuracy

## 📚 Additional Resources

- [Gemini API Documentation](https://ai.google.dev/docs)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [RAG Architecture Guide](https://www.anthropic.com/research/retrieval-augmented-generation)

## 🎉 Benefits Over Previous System

1. ✅ **Full conversation memory** - No more lost context
2. ✅ **Natural change handling** - Users can modify any detail anytime
3. ✅ **Better intent understanding** - Advanced NLU with Gemini 2.5 Flash
4. ✅ **Proactive suggestions** - System suggests alternatives automatically
5. ✅ **Persistent sessions** - Conversations survive server restarts
6. ✅ **Scalable architecture** - Database-backed, production-ready
7. ✅ **Better error handling** - Graceful degradation and recovery
8. ✅ **Richer context** - Real-time database retrieval for accurate information

## 🔐 Security Considerations

1. **API Key Protection**: Never commit API keys to version control
2. **Input Validation**: System validates all user inputs
3. **SQL Injection**: Uses Django ORM (protected)
4. **CSRF Protection**: CSRF exempt for API (consider adding token auth)
5. **Rate Limiting**: Consider adding rate limiting for production

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review code comments in source files
3. Check Django logs for errors
4. Review conversation history in admin panel

---

**Version:** 3.0 RAG
**Last Updated:** 2025-11-16
**Powered by:** Gemini 2.5 Flash + Django
**Architecture:** RAG (Retrieval-Augmented Generation)
