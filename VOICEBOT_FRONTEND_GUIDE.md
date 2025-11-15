# VoiceBot Frontend Integration - Quick Start Guide

## 🚀 5-Minute Setup

This guide shows you how to integrate the VoiceBot REST API into your frontend application.

---

## ✅ Prerequisites

1. **Backend running**: Start Django server on port 8000
   ```bash
   python manage.py runserver 8000
   ```

2. **Modern browser**: Chrome, Edge, or Safari (for Web Speech API support)

3. **HTTPS (production)**: Web Speech API requires HTTPS in production

---

## 📝 Minimal Working Example (Copy & Paste)

Save this as `voice-assistant.html` and open in your browser:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Assistant</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
        button { padding: 15px 30px; margin: 10px; font-size: 16px; cursor: pointer; }
        .message { padding: 10px; margin: 10px 0; border-radius: 10px; }
        .user { background: #007bff; color: white; text-align: right; }
        .bot { background: #f1f1f1; }
    </style>
</head>
<body>
    <h1>🤖 Voice Assistant</h1>
    <button onclick="start()">🎤 Start</button>
    <button onclick="stop()">⏹️ Stop</button>
    <div id="status">Ready</div>
    <div id="messages"></div>

    <script>
        const API = 'http://localhost:8000/voicebot/api/';
        let sessionId = 'voice_' + Date.now();
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'en-IN';

        recognition.onresult = (e) => {
            const text = e.results[e.results.length-1][0].transcript;
            send(text);
        };

        async function send(msg) {
            if (msg) add(msg, 'user');
            const res = await fetch(API, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg||'', session_id: sessionId})
            });
            const data = await res.json();
            add(data.message, 'bot');
            speak(data.message);
        }

        function add(text, type) {
            const div = document.createElement('div');
            div.className = 'message ' + type;
            div.textContent = text;
            document.getElementById('messages').appendChild(div);
        }

        function speak(text) {
            const u = new SpeechSynthesisUtterance(text);
            u.lang = 'en-IN';
            speechSynthesis.speak(u);
        }

        function start() {
            recognition.start();
            send('');
            document.getElementById('status').textContent = '🎤 Listening...';
        }

        function stop() {
            recognition.stop();
            document.getElementById('status').textContent = 'Stopped';
        }
    </script>
</body>
</html>
```

That's it! Open the file and click "Start".

---

## 🎯 API Reference

### Endpoint
```
POST http://localhost:8000/voicebot/api/
```

### Request
```json
{
  "message": "I have a headache",
  "session_id": "voice_1234567890"
}
```

### Response
```json
{
  "success": true,
  "session_id": "voice_1234567890",
  "message": "Based on your symptoms, I recommend Dr. Smith...",
  "stage": "doctor_selection",
  "action": "continue",
  "data": {...}
}
```

---

## 📚 Full Documentation

For complete examples, error handling, and advanced features, see:
- **[Complete API Documentation](./VOICEBOT_API_DOCUMENTATION.md)**

---

## 🔗 Quick Links

- API Docs: http://localhost:8000/voicebot/api/ (GET request)
- Health Check: http://localhost:8000/api/health/
- Main API Docs: http://localhost:8000/api/docs/

---

**That's all you need to get started!** 🎉

For production-ready implementation with error handling, see the complete documentation.
