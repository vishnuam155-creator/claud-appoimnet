# Voice Intelligence Assistant - Testing Guide

This guide provides multiple methods to verify that the Voice Intelligence Assistant is working correctly.

---

## 📋 Quick Verification Checklist

Before testing, ensure:
- ✅ All files are present in `/voicebot/` directory
- ✅ Django is installed: `pip install django google-generativeai`
- ✅ Gemini API key is configured in Django settings
- ✅ Database migrations are applied: `python manage.py migrate`
- ✅ Django server can start: `python manage.py runserver`

---

## Method 1: Run Automated Verification Script ⭐ (Easiest)

This script checks files, imports, and basic functionality without needing Django server.

```bash
# From project root directory
python verify_voice_intelligence.py
```

**What it checks:**
- ✅ All required files exist
- ✅ Modules can be imported
- ✅ Classes have required methods
- ✅ Voice understanding works
- ✅ URL patterns are configured

**Expected output:**
```
╔════════════════════════════════════════════════════════════╗
║   Voice Intelligence Assistant - Verification Script       ║
╚════════════════════════════════════════════════════════════╝

1. CHECKING FILES...
✓ voicebot/voice_intelligence_service.py
✓ voicebot/database_action_handler.py
...

🎉 ALL CHECKS PASSED!
Voice Intelligence Assistant is correctly implemented!
```

---

## Method 2: Test API Endpoints with Shell Script

This tests all API endpoints with real HTTP requests.

**Prerequisites:** Django server must be running.

```bash
# Terminal 1: Start Django server
python manage.py runserver

# Terminal 2: Run API tests
chmod +x test_voice_intelligence_api.sh
./test_voice_intelligence_api.sh
```

**What it tests:**
- Intent analysis endpoint
- Full voice intelligence processing
- Database action execution
- Mixed language support
- Error handling
- Session management
- Legacy compatibility

**Expected output:**
```
================================================
Voice Intelligence Assistant - API Test Suite
================================================

Testing: Intent Analysis - Simple Query
✓ PASSED

Testing: Voice Intelligence - Full Processing
✓ PASSED
...

Test Summary
Tests Passed: 10
Tests Failed: 0
✓ All tests passed!
```

---

## Method 3: Manual API Testing with curl

Test individual endpoints manually to see detailed responses.

### 3.1 Test Intent Analysis (No DB required)

```bash
curl -X POST http://localhost:8000/voicebot/api/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "I want to book an appointment tomorrow with Dr. Rahul"
  }'
```

**Expected response:**
```json
{
  "understood_input": {
    "corrected_text": "I want to book an appointment tomorrow with Dr. Rahul",
    "detected_language": "en",
    "extracted_entities": {
      "doctor_name": "Dr. Rahul",
      "date": "tomorrow"
    },
    "confidence": "high"
  },
  "intent": {
    "intent": "appointment_booking",
    "confidence": "high",
    "requires_database": true
  },
  "database_action": {
    "action": "query_database",
    "query_type": "create_appointment",
    "parameters": {
      "doctor_name": "Dr. Rahul",
      "date": "2025-11-14"
    }
  }
}
```

### 3.2 Test Full Voice Intelligence

```bash
curl -X POST http://localhost:8000/voicebot/api/intelligence/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "Hello, I need help booking an appointment"
  }'
```

**Expected response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "voice_response": "Welcome to MedCare Clinic! I'd be happy to help...",
  "action": "continue",
  "data": {
    "intent": {...},
    "conversation_context": {...}
  }
}
```

### 3.3 Test Mixed Language Support

```bash
curl -X POST http://localhost:8000/voicebot/api/intent-analysis/ \
  -H "Content-Type: application/json" \
  -d '{
    "voice_text": "Kal morning appointment chahiye Doctor Rahul se"
  }'
```

**Should detect intent correctly despite Hindi/English mix.**

### 3.4 Test Database Action (Appointment Lookup)

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

**Expected response:**
```json
{
  "success": true,
  "voice_response": "I found your appointment with Dr. Rahul...",
  "database_result": {
    "status": "success",
    "data": [...]
  }
}
```

### 3.5 Test Session Management

```bash
# Get session info
curl http://localhost:8000/voicebot/api/session/?session_id=test-123

# Delete session
curl -X DELETE http://localhost:8000/voicebot/api/session/?session_id=test-123
```

---

## Method 4: Django Shell Testing

Interactive testing in Django shell for deeper inspection.

```bash
python manage.py shell
```

**Test 1: Import and Initialize**
```python
from voicebot.voice_intelligence_manager import VoiceIntelligenceManager

manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")
print("✓ Manager initialized successfully")
```

**Test 2: Test Voice Understanding**
```python
result = manager.get_intent_and_action("Book appointment tomorrow with Dr. Rahul")

print("Intent:", result['intent']['intent'])
print("Action:", result['database_action']['action'])
print("Parameters:", result['database_action']['parameters'])
```

**Expected output:**
```
Intent: appointment_booking
Action: query_database
Parameters: {'doctor_name': 'Dr. Rahul', 'date': '2025-11-14', ...}
```

**Test 3: Test Full Processing**
```python
result = manager.process_voice_input("Hello, I need help")

print("Success:", result['success'])
print("Response:", result['voice_response'])
print("Session ID:", result['session_id'])
```

**Test 4: Test Multiple Scenarios**
```python
test_cases = [
    "Book appointment tomorrow 10 AM with Dr. Rahul",
    "Check my appointment with phone 9876543210",
    "Cancel my appointment",
    "I have fever and headache, which doctor should I see?",
]

for voice_text in test_cases:
    result = manager.get_intent_and_action(voice_text)
    print(f"\nInput: {voice_text}")
    print(f"Intent: {result['intent']['intent']}")
    print(f"Query type: {result['database_action'].get('query_type', 'N/A')}")
```

**Test 5: Test Database Handler Directly**
```python
from voicebot.database_action_handler import DatabaseActionHandler

handler = DatabaseActionHandler()

# Test doctor lookup
action = {
    "action": "query_database",
    "query_type": "get_doctors",
    "parameters": {}
}

result = handler.execute_action(action)
print("Status:", result['status'])
print("Doctors:", result['data'])
```

---

## Method 5: Browser Testing (Postman/Insomnia)

Use API testing tools for visual testing.

### Postman Collection Setup

1. Create new collection: "Voice Intelligence Tests"
2. Add requests:

**Request 1: Intent Analysis**
- Method: POST
- URL: `http://localhost:8000/voicebot/api/intent-analysis/`
- Body (JSON):
```json
{
  "voice_text": "Book appointment tomorrow"
}
```

**Request 2: Full Processing**
- Method: POST
- URL: `http://localhost:8000/voicebot/api/intelligence/`
- Body (JSON):
```json
{
  "voice_text": "I want to book appointment",
  "session_id": "{{session_id}}"
}
```

**Request 3: Database Action**
- Method: POST
- URL: `http://localhost:8000/voicebot/api/database-action/`
- Body (JSON):
```json
{
  "action": "query_database",
  "query_type": "appointment_lookup",
  "parameters": {
    "phone": "9876543210"
  }
}
```

---

## Method 6: Frontend Integration Test

Create a simple HTML page to test voice input.

**test_voice_ui.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Intelligence Test</title>
</head>
<body>
    <h1>Voice Intelligence Assistant Test</h1>

    <button id="startBtn">🎤 Start Speaking</button>
    <p id="transcript"></p>
    <p id="response"></p>

    <script>
        const startBtn = document.getElementById('startBtn');
        const transcript = document.getElementById('transcript');
        const response = document.getElementById('response');

        const recognition = new webkitSpeechRecognition();
        recognition.lang = 'en-IN';

        recognition.onresult = async (event) => {
            const text = event.results[0][0].transcript;
            transcript.textContent = 'You said: ' + text;

            // Send to API
            const res = await fetch('http://localhost:8000/voicebot/api/intelligence/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({voice_text: text})
            });

            const data = await res.json();
            response.textContent = 'Bot: ' + data.voice_response;

            // Speak response
            const utterance = new SpeechSynthesisUtterance(data.voice_response);
            speechSynthesis.speak(utterance);
        };

        startBtn.onclick = () => recognition.start();
    </script>
</body>
</html>
```

---

## Expected Test Results

### ✅ What Should Work

1. **Intent Detection:**
   - Booking: "Book appointment" → `appointment_booking`
   - Lookup: "Check my appointment" → `appointment_lookup`
   - Cancel: "Cancel appointment" → `appointment_cancel`
   - Doctor query: "Show me doctors" → `doctor_query`

2. **Entity Extraction:**
   - Names: "Dr. Rahul" → `{doctor_name: "Dr. Rahul"}`
   - Phones: "nine eight seven six five..." → `{phone: "9876543210"}`
   - Dates: "tomorrow" → `{date: "2025-11-14"}`
   - Times: "10 AM" → `{time: "10:00 AM"}`

3. **Mixed Language:**
   - Hindi-English mix should be corrected to English
   - Tamil-English mix should be understood
   - Malayalam-English mix should work

4. **Database Actions:**
   - JSON actions generated correctly
   - Parameters formatted properly
   - Database queries executed (if data exists)
   - Natural responses generated

5. **Error Handling:**
   - Empty input rejected
   - Invalid JSON handled
   - Missing data triggers clarification
   - Database errors handled gracefully

---

## Troubleshooting

### Issue 1: ModuleNotFoundError: No module named 'google.generativeai'

**Solution:**
```bash
pip install google-generativeai
```

### Issue 2: "ANTHROPIC_API_KEY not set"

**Solution:** Add to `settings.py`:
```python
ANTHROPIC_API_KEY = 'your-gemini-api-key-here'
```

### Issue 3: Database queries fail

**Reason:** No data in database.

**Solution:** This is normal for fresh setup. Intent detection and JSON generation will still work.

### Issue 4: Import errors

**Solution:**
```bash
# Make sure you're in the right directory
cd /home/user/claud-appoimnet

# Activate virtual environment if you have one
source venv/bin/activate  # or your venv path

# Install requirements
pip install -r requirements.txt
```

### Issue 5: API returns 404

**Check:**
- Django server is running
- URL patterns are included in main urls.py
- Accessing correct URL: `http://localhost:8000/voicebot/api/...`

---

## Performance Benchmarks

### Expected Response Times:
- **Intent Analysis:** < 2 seconds
- **Full Processing (no DB):** < 3 seconds
- **Database Action:** < 5 seconds
- **Session Operations:** < 100ms

### API Limits:
- Gemini AI calls: Rate limited by Google
- Session storage: In-memory (1 hour timeout)
- Database queries: Standard Django ORM performance

---

## Continuous Integration Testing

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
name: Voice Intelligence Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python verify_voice_intelligence.py
      - run: python manage.py test voicebot
```

---

## Success Criteria

Your implementation is **correctly working** if:

1. ✅ `verify_voice_intelligence.py` shows all checks passed
2. ✅ API endpoints return proper JSON responses
3. ✅ Intent detection works for various inputs
4. ✅ JSON actions are generated correctly
5. ✅ Database operations execute (or fail gracefully with no data)
6. ✅ Natural language responses are generated
7. ✅ Session management works
8. ✅ Error handling works properly
9. ✅ Mixed language inputs are understood
10. ✅ Documentation is clear and examples work

---

## Next Steps After Verification

Once all tests pass:

1. **Configure Production Settings:**
   - Set up Redis for session storage
   - Add authentication
   - Enable HTTPS
   - Configure rate limiting

2. **Deploy:**
   - Deploy to production server
   - Set environment variables
   - Run migrations
   - Test with real users

3. **Monitor:**
   - Set up logging
   - Monitor API usage
   - Track success rates
   - Collect user feedback

4. **Optimize:**
   - Fine-tune AI prompts
   - Optimize database queries
   - Add caching where needed
   - Improve response times

---

## Support

If tests fail or you encounter issues:

1. Check the detailed error messages
2. Review `voicebot/README_VOICE_INTELLIGENCE.md`
3. Check `voicebot/VOICE_INTELLIGENCE_EXAMPLES.md`
4. Enable Django debug mode for detailed errors
5. Check Django logs: `python manage.py runserver --verbosity 3`

---

**Version:** 1.0.0
**Last Updated:** November 2025
