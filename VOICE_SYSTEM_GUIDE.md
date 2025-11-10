# Voice System Guide for Medical Appointment Booking

## Overview

The voice system enables patients to book medical appointments using voice input and receive voice-guided instructions throughout the booking process. This feature is designed to assist patients who prefer voice interaction over typing, making the system more accessible.

## Features

### 1. Voice Input (Speech-to-Text)
- Click the 🎤 microphone button to start voice recording
- Speak naturally to describe symptoms, select doctors, or provide information
- The system automatically transcribes your speech to text
- High-confidence transcriptions are automatically sent

### 2. Voice Output (Text-to-Speech)
- Click the 🔊 speaker button to enable voice output
- Bot responses will be read aloud automatically
- Click again (🔇) to disable voice output
- Voice continues while you navigate through booking steps

### 3. Voice-Guided Booking Flow
The system provides detailed voice guidance at each stage:

1. **Greeting**: Welcome message and introduction
2. **Symptoms**: Prompts for health concerns
3. **Doctor Selection**: Reads available doctors
4. **Date Selection**: Guides date picking
5. **Time Selection**: Presents available time slots
6. **Patient Details**: Requests contact information
7. **Confirmation**: Reviews booking details
8. **Completion**: Confirms successful booking

## Technical Implementation

### Browser-Based (Default - Free)
Uses Web Speech API built into modern browsers:
- **Requirements**: Chrome, Edge, or Safari browser
- **Cost**: Free
- **Setup**: No configuration needed
- **Language**: English (India), Hindi, English (US)

### Google Cloud (Optional - Advanced)
For production environments with high accuracy needs:
- **Requirements**: Google Cloud account with Speech APIs enabled
- **Cost**: Pay-per-use (see Google Cloud pricing)
- **Setup**: Requires service account and API keys
- **Language**: Multiple Indian languages supported

## Setup Instructions

### Quick Start (Browser-Based - Recommended)

1. **Access the chatbot**:
   ```
   http://localhost:8000/chatbot/
   ```

2. **Enable voice features**:
   - Click 🎤 to use voice input
   - Click 🔊 to hear responses

3. **Start speaking**:
   - The system will listen and transcribe
   - Speak clearly and naturally
   - Works best in quiet environments

### Advanced Setup (Google Cloud)

If you need production-grade voice recognition:

1. **Create Google Cloud Project**:
   ```bash
   # Visit: https://console.cloud.google.com/
   # Create new project
   # Enable Cloud Speech-to-Text API
   # Enable Cloud Text-to-Speech API
   ```

2. **Create Service Account**:
   ```bash
   # Create service account
   # Download JSON key file
   # Save as: /path/to/service-account-key.json
   ```

3. **Configure Environment**:
   ```bash
   # Add to .env file
   USE_GOOGLE_CLOUD_SPEECH=True
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   ```

4. **Install Dependencies**:
   ```bash
   pip install google-cloud-speech google-cloud-texttospeech
   ```

5. **Restart Server**:
   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Voice API Endpoint
```
POST /api/voice/
```

#### Actions:

**1. Transcribe Audio (Speech-to-Text)**
```json
{
  "action": "transcribe",
  "audio_data": "base64_encoded_audio",
  "audio_format": "webm"
}
```

Response:
```json
{
  "success": true,
  "text": "I have a headache and fever",
  "confidence": 0.95
}
```

**2. Synthesize Speech (Text-to-Speech)**
```json
{
  "action": "synthesize",
  "text": "Your appointment is confirmed",
  "language": "en-IN"
}
```

Response:
```json
{
  "success": true,
  "audio_data": "base64_encoded_audio",
  "audio_format": "mp3"
}
```

**3. Get Voice Guidance**
```json
{
  "action": "voice_guidance",
  "stage": "symptoms"
}
```

Response:
```json
{
  "success": true,
  "guidance": "Please describe your symptoms..."
}
```

## User Interface

### Voice Controls

| Button | Function | State |
|--------|----------|-------|
| 🎤 (Green) | Start voice recording | Ready |
| 🎤 (Red, pulsing) | Currently recording | Active |
| 🔊 (Blue) | Voice output enabled | On |
| 🔇 (Gray) | Voice output disabled | Off |

### Voice Status Indicator
- Appears above the input area during voice operations
- Shows status: "Listening...", "Speaking...", etc.
- Auto-hides when inactive

## Configuration

### Settings (config/settings.py)

```python
# Use Google Cloud Speech API (optional)
USE_GOOGLE_CLOUD_SPEECH = False  # Set to True for Google Cloud

# Default language for voice
VOICE_LANGUAGE_DEFAULT = 'en-IN'

# Supported languages
VOICE_SUPPORTED_LANGUAGES = ['en-IN', 'hi-IN', 'en-US']

# Speaking rate (0.5 to 2.0)
VOICE_SPEAKING_RATE = 0.95

# Auto-speak responses
VOICE_ENABLE_AUTO_SPEAK = False
```

### Environment Variables (.env)

```bash
# Optional: Google Cloud Speech API
USE_GOOGLE_CLOUD_SPEECH=False
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Voice settings
VOICE_LANGUAGE_DEFAULT=en-IN
VOICE_SPEAKING_RATE=0.95
```

## Code Structure

```
claud-appoimnet/
├── chatbot/
│   └── voice_service.py          # Voice service backend
├── patient_booking/
│   ├── views.py                  # Voice API endpoints
│   └── urls.py                   # Voice URL routing
├── templates/patient_booking/
│   └── chatbot.html              # Voice UI and JavaScript
└── config/
    └── settings.py               # Voice configuration
```

## Usage Examples

### Example 1: Voice-Only Booking
1. Open chatbot page
2. Click 🔊 to enable voice output
3. Click 🎤 and say: "I need a doctor"
4. Listen to the response
5. Click 🎤 and say: "I have back pain"
6. Continue voice conversation to complete booking

### Example 2: Mixed Input (Voice + Text)
1. Click 🎤 to describe symptoms by voice
2. Type to select doctor name
3. Click 🎤 to provide contact details
4. Use buttons to confirm appointment

### Example 3: Voice Guidance
1. Enable voice output (🔊)
2. Type messages as usual
3. Listen to detailed voice instructions
4. Follow voice prompts for each step

## Browser Compatibility

| Browser | Voice Input | Voice Output | Notes |
|---------|-------------|--------------|-------|
| Chrome | ✅ Yes | ✅ Yes | Best support |
| Edge | ✅ Yes | ✅ Yes | Full support |
| Safari | ✅ Yes | ✅ Yes | iOS support |
| Firefox | ⚠️ Limited | ✅ Yes | Input experimental |
| Opera | ✅ Yes | ✅ Yes | Chromium-based |

## Troubleshooting

### Voice Input Not Working

**Issue**: Microphone button does nothing
- **Solution**: Check browser permissions for microphone access
- **Solution**: Use Chrome, Edge, or Safari
- **Solution**: Ensure HTTPS or localhost (required for Web Speech API)

**Issue**: "No speech detected" error
- **Solution**: Speak louder and closer to microphone
- **Solution**: Check microphone settings in OS
- **Solution**: Reduce background noise

### Voice Output Not Working

**Issue**: No sound when 🔊 is enabled
- **Solution**: Check system volume
- **Solution**: Ensure browser has permission to play audio
- **Solution**: Try refreshing the page

**Issue**: Voice sounds robotic or unnatural
- **Solution**: Install Google Cloud TTS for better voices
- **Solution**: Adjust VOICE_SPEAKING_RATE in settings

### Google Cloud Issues

**Issue**: "Google Cloud not available" error
- **Solution**: Verify service account JSON file path
- **Solution**: Check API keys are enabled in Google Cloud Console
- **Solution**: Ensure billing is enabled for the project

## Performance & Cost

### Browser-Based (Web Speech API)
- **Cost**: $0 (Free)
- **Latency**: ~500ms
- **Accuracy**: 85-95% (good)
- **Limits**: None
- **Recommended for**: Development, testing, small deployments

### Google Cloud Speech API
- **Cost**: $0.006 per 15 seconds (STT), $4-16 per 1M chars (TTS)
- **Latency**: ~200ms
- **Accuracy**: 95-99% (excellent)
- **Limits**: API quotas apply
- **Recommended for**: Production, high-volume, multi-language

## Security Considerations

1. **Microphone Access**: Users must grant permission
2. **Audio Data**: Not stored on server (processed in-memory)
3. **Privacy**: Voice data sent to Google Cloud (if enabled)
4. **HTTPS**: Required for Web Speech API to work
5. **CORS**: Configured for localhost only by default

## Future Enhancements

- [ ] Multi-language support (Hindi, Tamil, Telugu, etc.)
- [ ] Voice authentication for patient verification
- [ ] Offline voice recognition
- [ ] Voice commands (e.g., "go back", "cancel", "repeat")
- [ ] Emotion detection from voice
- [ ] Voice prescription reading
- [ ] Voice-based medication reminders

## Support

For issues or questions:
1. Check browser console for errors (F12)
2. Review Django logs for backend errors
3. Test microphone with other apps
4. Verify API credentials if using Google Cloud

## Version History

- **v1.0** (2024-01-10): Initial voice system release
  - Web Speech API integration
  - Google Cloud Speech API support
  - Voice-guided booking flow
  - Multi-language support (en-IN, hi-IN, en-US)
