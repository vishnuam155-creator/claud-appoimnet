# Voice Provider and Asterisk Telephony Integration

## Overview

This update adds comprehensive voice provider support and telephony integration to the MediBot Voice Assistant, enabling:

- **Multiple Voice Providers**: Choose between Browser API, Google Cloud, or AI4Bharat
- **Indian Language Support**: Native support for Hindi, Tamil, Telugu, and other Indian languages via AI4Bharat
- **Telephony Integration**: Handle real phone calls through Asterisk PBX integration
- **Flexible Configuration**: Easy switching between providers via settings UI

## What's New

### 1. AI4Bharat Integration
- Speech-to-Text (STT) for Indian languages
- Text-to-Speech (TTS) with natural voices
- Support for 10+ Indian languages
- Better accuracy for regional languages

### 2. Asterisk PBX Integration
- Handle incoming phone calls
- Make outbound appointment reminder calls
- AGI and ARI interface support
- Real-time call processing with voicebot

### 3. Unified Voice Service
- Single interface for all voice providers
- Automatic provider fallback
- Session-based provider preferences
- Server-side and client-side processing

### 4. Enhanced UI
- Settings modal for voice provider selection
- Language selection based on provider
- Connection testing
- Real-time status updates

## Quick Start

### 1. Basic Setup (Browser API - Default)

No configuration needed! The browser API works out of the box.

```bash
python manage.py runserver
```

Visit http://localhost:8000/voicebot/ and start using voice assistant.

### 2. Enable AI4Bharat (Recommended for Indian Languages)

Add to `.env`:

```bash
AI4BHARAT_API_KEY=your_api_key_here
VOICE_PROVIDER=ai4bharat
```

Restart server and select AI4Bharat in settings.

### 3. Enable Asterisk (For Phone Calls)

Install and configure Asterisk:

```bash
# Install Asterisk
sudo apt-get install asterisk

# Configure (see docs/asterisk_config_example.conf)
sudo vim /etc/asterisk/ari.conf

# Add to .env
ASTERISK_ENABLED=True
ASTERISK_ARI_URL=http://localhost:8088/ari
ASTERISK_ARI_USERNAME=voicebot
ASTERISK_ARI_PASSWORD=your_password
```

## File Structure

```
├── chatbot/
│   └── ai4bharat_voice_service.py      # AI4Bharat integration
├── voicebot/
│   ├── asterisk_telephony_service.py   # Asterisk integration
│   ├── asterisk_views.py               # Asterisk API endpoints
│   ├── voice_provider_views.py         # Voice provider APIs
│   ├── unified_voice_service.py        # Unified voice interface
│   └── templates/voicebot/
│       └── voice_assistant.html        # Updated UI with settings
├── config/
│   └── settings.py                     # Updated configuration
├── docs/
│   ├── VOICE_PROVIDER_INTEGRATION.md   # Complete documentation
│   └── asterisk_config_example.conf    # Asterisk config template
└── VOICE_INTEGRATION_README.md         # This file
```

## Key Features

### Voice Provider Selection

Users can choose their preferred voice provider:

1. **Browser Speech API** (Default)
   - Free, no setup required
   - Works offline
   - Good for web-based usage

2. **Google Cloud Speech**
   - High accuracy
   - 100+ languages
   - Requires API key

3. **AI4Bharat**
   - Optimized for Indian languages
   - Better regional language accuracy
   - Requires API key

### Language Support

**Browser & Google:**
- English (India)
- Hindi
- English (US)

**AI4Bharat:**
- Hindi (हिन्दी)
- Tamil (தமிழ்)
- Telugu (తెలుగు)
- Bengali (বাংলা)
- Marathi (मराठी)
- Gujarati (ગુજરાતી)
- Kannada (ಕನ್ನಡ)
- Malayalam (മലയാളം)
- Punjabi (ਪੰਜਾਬੀ)
- English

### Asterisk Telephony

Enable phone call handling:

- Receive incoming calls
- Make outbound calls
- Process voice in real-time
- Integrate with existing PBX systems

## API Endpoints

### Voice Provider

```bash
# Get configuration
GET /voicebot/api/voice-provider/config/

# Set provider
POST /voicebot/api/voice-provider/config/
{"provider": "ai4bharat"}

# Test connection
POST /voicebot/api/voice-provider/test/
{"provider": "ai4bharat"}
```

### AI4Bharat

```bash
# Speech to text
POST /voicebot/api/ai4bharat/stt/
(multipart/form-data with audio file)

# Text to speech
POST /voicebot/api/ai4bharat/tts/
{"text": "नमस्ते", "language": "hi"}

# Get languages
GET /voicebot/api/ai4bharat/languages/
```

### Asterisk

```bash
# Handle incoming call
POST /voicebot/api/asterisk/incoming/
{"channel_id": "...", "caller_id": "..."}

# Process audio
POST /voicebot/api/asterisk/process/
(multipart with audio + session data)

# Make outbound call
POST /voicebot/api/asterisk/outbound/
{"phone_number": "9876543210", "message": "..."}

# Active calls
GET /voicebot/api/asterisk/active-calls/

# End call
POST /voicebot/api/asterisk/end-call/
{"session_id": "..."}
```

## Configuration

### Environment Variables

```bash
# Voice Provider Selection
VOICE_PROVIDER=browser  # browser, google, ai4bharat

# AI4Bharat Configuration
AI4BHARAT_API_KEY=your_key
AI4BHARAT_DEFAULT_LANGUAGE=hi
AI4BHARAT_VOICE_GENDER=female
AI4BHARAT_SPEAKING_RATE=1.0

# Asterisk Configuration
ASTERISK_ENABLED=False
ASTERISK_ARI_URL=http://localhost:8088/ari
ASTERISK_ARI_USERNAME=voicebot
ASTERISK_ARI_PASSWORD=secure_password
ASTERISK_ARI_APP=voicebot
ASTERISK_RECORDING_PATH=/var/spool/asterisk/recording
ASTERISK_AUDIO_PATH=/var/lib/asterisk/sounds/custom
```

## Usage Examples

### Frontend - Change Voice Provider

```javascript
// Open settings
openVoiceSettings();

// Or programmatically
fetch('/voicebot/api/voice-provider/config/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider: 'ai4bharat' })
});
```

### Backend - Use Unified Voice Service

```python
from voicebot.unified_voice_service import get_unified_voice_service

# Get service with auto-detection
voice_service = get_unified_voice_service(session_data=session_data)

# Speech to text
result = voice_service.speech_to_text(audio_data, language='hi')
print(result['transcript'])

# Text to speech
result = voice_service.text_to_speech("नमस्ते", language='hi')
audio_data = result['audio_data']
```

### Asterisk - Handle Incoming Call

```python
from voicebot.asterisk_telephony_service import get_asterisk_service

asterisk = get_asterisk_service()

# Register voicebot callback
def process_audio(audio_data, session_id, caller_id):
    # Your voicebot processing logic
    return {
        'text': 'Response text',
        'audio_file': 'path/to/response.wav',
        'action': 'continue'
    }

asterisk.register_voicebot_callback(process_audio)

# Handle call
result = asterisk.handle_incoming_call_ari(channel_id, caller_id)
```

## Testing

### Test AI4Bharat

```bash
# Test connection
curl -X POST http://localhost:8000/voicebot/api/voice-provider/test/ \
  -H "Content-Type: application/json" \
  -d '{"provider": "ai4bharat"}'

# Test STT
curl -X POST http://localhost:8000/voicebot/api/ai4bharat/stt/ \
  -F "audio=@test.wav" \
  -F "language=hi"
```

### Test Asterisk

```bash
# Check ARI status
curl -u voicebot:password http://localhost:8088/ari/channels

# Test incoming call endpoint
curl -X POST http://localhost:8000/voicebot/api/asterisk/incoming/ \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "test-123", "caller_id": "9876543210"}'
```

## Documentation

Complete documentation available in:
- `docs/VOICE_PROVIDER_INTEGRATION.md` - Full integration guide
- `docs/asterisk_config_example.conf` - Asterisk configuration template

## Support

For issues or questions:
- Check documentation in `docs/` folder
- Review troubleshooting section in integration guide
- Open GitHub issue

## Next Steps

1. **Get AI4Bharat API Key**: Visit https://ai4bharat.org/
2. **Configure Asterisk**: Follow guide in `docs/asterisk_config_example.conf`
3. **Test Integration**: Use test endpoints to verify setup
4. **Deploy**: Update production environment variables

## License

Part of MediBot Voice Assistant project.

## Contributors

- Initial implementation: Claude AI
- Integration: MediBot Development Team
