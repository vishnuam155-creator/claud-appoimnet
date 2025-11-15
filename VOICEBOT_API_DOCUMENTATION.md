# VoiceBot REST API Documentation
## Google Gemini 2.5 Flash Powered Natural Conversational Appointment Booking

**Version:** 2.0
**AI Model:** Google Gemini 2.5 Flash
**Type:** Pure REST API (No Template Rendering)

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Format](#requestresponse-format)
4. [Conversation Flow](#conversation-flow)
5. [Frontend Integration](#frontend-integration)
6. [Code Examples](#code-examples)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

---

## 🎯 Overview

The VoiceBot REST API provides a natural conversational interface for booking medical appointments using voice input. Powered by Google Gemini 2.5 Flash AI, it understands natural language, analyzes symptoms, suggests doctors, and completes appointment bookings through multi-turn conversations.

### Key Features
- ✅ Natural language understanding with Gemini 2.5 Flash AI
- ✅ Intelligent doctor matching by name or symptoms
- ✅ Smart date/time parsing (supports natural language)
- ✅ Context-aware multi-turn conversation flow
- ✅ Intent detection and automatic correction handling
- ✅ Mid-conversation symptom change detection
- ✅ Complete appointment booking workflow
- ✅ Real-time availability checking
- ✅ Session-based conversation memory

---

## 🔌 API Endpoints

### 1. Voice Assistant API

#### **GET** `/voicebot/api/`
Returns comprehensive API documentation and usage guide.

**Response:**
```json
{
  "success": true,
  "message": "Voice Assistant REST API...",
  "version": "2.0",
  "api_info": {...},
  "request_format": {...},
  "response_format": {...},
  "features": [...],
  "conversation_stages": [...],
  "example_usage": {...}
}
```

#### **POST** `/voicebot/api/`
Process voice input and return AI-generated response.

**Request Body:**
```json
{
  "message": "I have a headache",
  "session_id": "voice_1234567890",  // Optional
  "session_data": {}                  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "voice_1234567890",
  "message": "Based on your symptoms, I recommend Dr. Smith...",
  "stage": "doctor_selection",
  "action": "continue",
  "data": {
    "stage": "doctor_selection",
    "patient_name": "John",
    "suggested_doctors": [...]
  }
}
```

### 2. Voice Intelligence API

#### **POST** `/voicebot/api/intelligence/`
Advanced voice intelligence processing with intent-to-action architecture.

#### **POST** `/voicebot/api/database-action/`
Execute database actions directly (for advanced integrations).

#### **POST** `/voicebot/api/intent-analysis/`
Analyze user intent without executing actions.

#### **GET/DELETE** `/voicebot/api/session/`
Manage conversation sessions.

---

## 📝 Request/Response Format

### Request Format

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `message` | string | ✅ Yes | User voice input (transcribed to text) | "I have a headache" |
| `session_id` | string | ❌ No | Session identifier (auto-generated if not provided) | "voice_1234567890" |
| `session_data` | object | ❌ No | Conversation context (managed automatically) | `{}` |

### Response Format

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Operation success status |
| `session_id` | string | Session identifier for conversation continuity |
| `message` | string | AI response message (ready for TTS) |
| `stage` | string | Current conversation stage |
| `action` | string | Action type (continue/booking_complete/error) |
| `data` | object | Session data containing collected information |

### Response Actions

| Action | Description |
|--------|-------------|
| `continue` | Continue to next stage of conversation |
| `booking_complete` | Appointment booking successfully completed |
| `cancelled` | User cancelled the booking |
| `error` | Error occurred during processing |

---

## 🔄 Conversation Flow

### Stage Progression

```
1. greeting
   ↓
2. patient_name (collects: patient_name)
   ↓
3. doctor_selection (collects: doctor_id, doctor_name)
   ↓
4. date_selection (collects: appointment_date)
   ↓
5. time_selection (collects: appointment_time)
   ↓
6. phone_collection (collects: phone)
   ↓
7. confirmation (reviews all details)
   ↓
8. completed (collects: appointment_id)
```

### Stage Details

| Stage | Description | User Input Example | AI Response Example |
|-------|-------------|-------------------|---------------------|
| `greeting` | Initial welcome | `""` (empty) | "Hello! Welcome to MediCare Clinic..." |
| `patient_name` | Name collection | "My name is John" | "Nice to meet you, John!" |
| `doctor_selection` | Doctor selection | "I have a headache" | "I recommend Dr. Smith, our Neurologist..." |
| `date_selection` | Date selection | "Tomorrow" | "Great! I have available slots tomorrow..." |
| `time_selection` | Time selection | "10 AM" | "Perfect! I'll book you for 10:00 AM..." |
| `phone_collection` | Phone collection | "9876543210" | "Thank you! Let me confirm your details..." |
| `confirmation` | Final confirmation | "Yes, confirm" | "Appointment booked! Your ID is APT12345..." |
| `completed` | Booking complete | - | "Thank you! See you on [date]..." |

---

## 💻 Frontend Integration

### Technology Stack Options

1. **React + react-speech-recognition**
2. **Vue.js + vue-speech**
3. **Vanilla JavaScript + Web Speech API**

### CORS Configuration

The API has CORS enabled for:
- `http://localhost:3000` (React default)
- `http://localhost:8080` (Vue default)

---

## 📚 Code Examples

### Example 1: Vanilla JavaScript with Web Speech API

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Assistant</title>
</head>
<body>
    <button id="startBtn">Start Conversation</button>
    <div id="transcript"></div>
    <div id="response"></div>

    <script>
        let sessionId = 'voice_' + Date.now();
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-IN';

        let finalTranscript = '';

        recognition.onresult = (event) => {
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript + ' ';
                } else {
                    interimTranscript += transcript;
                }
            }

            document.getElementById('transcript').textContent = interimTranscript || finalTranscript;

            // Process after 1.5 seconds of silence
            if (finalTranscript.trim()) {
                setTimeout(() => {
                    processVoiceInput(finalTranscript.trim());
                    finalTranscript = '';
                }, 1500);
            }
        };

        async function processVoiceInput(message) {
            recognition.stop();

            const response = await fetch('http://localhost:8000/voicebot/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            // Display response
            document.getElementById('response').textContent = data.message;

            // Speak response
            const utterance = new SpeechSynthesisUtterance(data.message);
            utterance.lang = 'en-IN';
            speechSynthesis.speak(utterance);

            // Resume listening after speaking
            utterance.onend = () => {
                if (data.action !== 'booking_complete') {
                    recognition.start();
                }
            };
        }

        document.getElementById('startBtn').onclick = () => {
            recognition.start();
            processVoiceInput(''); // Start conversation
        };
    </script>
</body>
</html>
```

### Example 2: React with Fetch API

```jsx
import React, { useState, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

const VoiceAssistant = () => {
  const [sessionId] = useState(`voice_${Date.now()}`);
  const [messages, setMessages] = useState([]);
  const { transcript, resetTranscript } = useSpeechRecognition();

  const processVoiceInput = async (message) => {
    if (!message) return;

    // Add user message
    setMessages(prev => [...prev, { type: 'user', text: message }]);

    // Call API
    const response = await fetch('http://localhost:8000/voicebot/api/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        session_id: sessionId
      })
    });

    const data = await response.json();

    // Add bot response
    setMessages(prev => [...prev, { type: 'bot', text: data.message }]);

    // Speak response
    const utterance = new SpeechSynthesisUtterance(data.message);
    utterance.lang = 'en-IN';
    speechSynthesis.speak(utterance);

    resetTranscript();
  };

  useEffect(() => {
    if (transcript) {
      const timer = setTimeout(() => {
        processVoiceInput(transcript);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [transcript]);

  const startListening = () => {
    SpeechRecognition.startListening({ continuous: true, language: 'en-IN' });
    processVoiceInput(''); // Start conversation
  };

  const stopListening = () => {
    SpeechRecognition.stopListening();
  };

  return (
    <div>
      <h1>Voice Assistant</h1>
      <button onClick={startListening}>Start</button>
      <button onClick={stopListening}>Stop</button>

      <div>
        <p>Listening: {transcript}</p>
      </div>

      <div>
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.type}>
            {msg.text}
          </div>
        ))}
      </div>
    </div>
  );
};

export default VoiceAssistant;
```

### Example 3: Vue.js with Axios

```vue
<template>
  <div class="voice-assistant">
    <h1>Voice Assistant</h1>
    <button @click="startConversation">Start Conversation</button>
    <button @click="stopConversation">Stop</button>

    <div class="transcript">
      <p>You: {{ transcript }}</p>
    </div>

    <div class="messages">
      <div v-for="(msg, index) in messages" :key="index" :class="msg.type">
        {{ msg.text }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'VoiceAssistant',
  data() {
    return {
      sessionId: `voice_${Date.now()}`,
      transcript: '',
      messages: [],
      recognition: null,
      isListening: false
    };
  },
  methods: {
    initSpeechRecognition() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-IN';

      let finalTranscript = '';

      this.recognition.onresult = (event) => {
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        this.transcript = interimTranscript || finalTranscript;

        if (finalTranscript.trim()) {
          setTimeout(() => {
            this.processVoiceInput(finalTranscript.trim());
            finalTranscript = '';
          }, 1500);
        }
      };
    },
    async processVoiceInput(message) {
      if (!message && this.messages.length > 0) return;

      if (message) {
        this.messages.push({ type: 'user', text: message });
      }

      try {
        const response = await axios.post('http://localhost:8000/voicebot/api/', {
          message: message || '',
          session_id: this.sessionId
        });

        const data = response.data;
        this.messages.push({ type: 'bot', text: data.message });

        // Text-to-Speech
        const utterance = new SpeechSynthesisUtterance(data.message);
        utterance.lang = 'en-IN';
        window.speechSynthesis.speak(utterance);

        this.transcript = '';
      } catch (error) {
        console.error('Error:', error);
        this.messages.push({ type: 'bot', text: 'Sorry, an error occurred.' });
      }
    },
    startConversation() {
      if (!this.recognition) {
        this.initSpeechRecognition();
      }
      this.recognition.start();
      this.isListening = true;
      this.processVoiceInput(''); // Initial greeting
    },
    stopConversation() {
      if (this.recognition) {
        this.recognition.stop();
      }
      this.isListening = false;
    }
  },
  mounted() {
    this.initSpeechRecognition();
  }
};
</script>

<style scoped>
.voice-assistant {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.messages {
  margin-top: 20px;
}

.user {
  background: #007bff;
  color: white;
  padding: 10px;
  margin: 10px 0;
  border-radius: 10px;
  text-align: right;
}

.bot {
  background: #f1f1f1;
  padding: 10px;
  margin: 10px 0;
  border-radius: 10px;
}
</style>
```

### Example 4: Python Client

```python
import requests
import json

class VoiceBotClient:
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url
        self.session_id = f"voice_{int(time.time())}"
        self.session_data = {}

    def send_message(self, message):
        """Send message to voicebot API"""
        url = f"{self.base_url}/voicebot/api/"

        payload = {
            "message": message,
            "session_id": self.session_id,
            "session_data": self.session_data
        }

        response = requests.post(url, json=payload)
        data = response.json()

        # Update session data
        self.session_data = data.get('data', {})

        return data

    def start_conversation(self):
        """Start a new conversation"""
        return self.send_message('')

    def get_api_info(self):
        """Get API documentation"""
        url = f"{self.base_url}/voicebot/api/"
        response = requests.get(url)
        return response.json()

# Usage
client = VoiceBotClient()

# Get API info
info = client.get_api_info()
print("API Version:", info['version'])

# Start conversation
response = client.start_conversation()
print("Bot:", response['message'])

# Continue conversation
response = client.send_message("My name is John")
print("Bot:", response['message'])

response = client.send_message("I have a headache")
print("Bot:", response['message'])
```

---

## ⚠️ Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": "Error type or message",
  "message": "User-friendly error message"
}
```

### Common Errors

| HTTP Status | Error | Cause | Solution |
|-------------|-------|-------|----------|
| 400 | Invalid JSON | Malformed JSON in request body | Validate JSON format before sending |
| 400 | Message required | Missing `message` field | Include `message` field (can be empty string for initial greeting) |
| 500 | AI Processing Error | Gemini AI error or backend issue | Retry request or show user-friendly error |
| 404 | Endpoint not found | Wrong URL | Use `/voicebot/api/` |

### Error Handling Example

```javascript
async function processVoiceInput(message) {
  try {
    const response = await fetch('http://localhost:8000/voicebot/api/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        session_id: sessionId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data.success) {
      console.error('API Error:', data.error);
      return {
        message: data.message || 'An error occurred. Please try again.',
        action: 'error'
      };
    }

    return data;

  } catch (error) {
    console.error('Network Error:', error);
    return {
      message: 'Connection error. Please check your internet and try again.',
      action: 'error'
    };
  }
}
```

---

## 🎯 Best Practices

### 1. Session Management
- Generate unique session IDs for each conversation
- Persist session ID throughout the conversation
- Clear session after booking completion

### 2. Voice Recognition
- Use silence detection (1-2 seconds) to trigger processing
- Support both continuous and discrete speech recognition
- Handle recognition errors gracefully

### 3. Text-to-Speech
- Use appropriate voice (preferably female for friendliness)
- Set speaking rate to 0.9-1.0 for clarity
- Wait for speech to complete before resuming listening

### 4. User Experience
- Show visual feedback during listening/processing
- Display conversation history
- Provide option to type if voice fails
- Allow users to correct mistakes

### 5. Error Recovery
- Retry failed requests with exponential backoff
- Provide clear error messages
- Allow users to restart conversation

### 6. Performance
- Implement request timeout (30 seconds recommended)
- Cache session data locally
- Debounce voice input processing

---

## 🔒 Security Considerations

1. **API Key Management**: Store API keys securely (not in frontend code)
2. **Rate Limiting**: Implement rate limiting on frontend to prevent abuse
3. **Input Validation**: Validate user input before sending to API
4. **HTTPS**: Use HTTPS in production
5. **Session Timeout**: Implement session expiration (1 hour recommended)

---

## 📊 Testing

### Manual Testing with cURL

```bash
# Get API documentation
curl -X GET http://localhost:8000/voicebot/api/

# Start conversation
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "",
    "session_id": "test_session_123"
  }'

# Send patient name
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My name is John",
    "session_id": "test_session_123"
  }'

# Describe symptoms
curl -X POST http://localhost:8000/voicebot/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a severe headache",
    "session_id": "test_session_123"
  }'
```

---

## 📞 Support & Contact

For issues, questions, or feature requests:
- Check the API documentation: `GET /voicebot/api/`
- Check the main API docs: `GET /api/docs/`
- Review the codebase documentation

---

## 📄 License

This API is part of the Medical Appointment Booking System.

---

**Last Updated:** November 2025
**API Version:** 2.0
**AI Model:** Google Gemini 2.5 Flash
