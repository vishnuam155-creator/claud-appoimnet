# Voice Provider and Asterisk Telephony Integration

This document explains how to integrate AI4Bharat voice services and Asterisk telephony with the MediBot Voice Assistant.

## Table of Contents

1. [Overview](#overview)
2. [Voice Provider Options](#voice-provider-options)
3. [AI4Bharat Integration](#ai4bharat-integration)
4. [Asterisk Telephony Integration](#asterisk-telephony-integration)
5. [Configuration Guide](#configuration-guide)
6. [API Endpoints](#api-endpoints)
7. [Frontend Usage](#frontend-usage)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The voicebot now supports multiple voice providers and telephony integration:

- **Browser Speech API** - Built-in browser speech recognition (default, free)
- **Google Cloud Speech** - Google's cloud-based STT/TTS services
- **AI4Bharat** - Indian language models for speech processing
- **Asterisk PBX** - Telephony integration for phone call handling

---

## Voice Provider Options

### 1. Browser Speech API (Default)

**Features:**
- ✅ Free, no API keys required
- ✅ Works offline
- ✅ No setup needed
- ⚠️ Limited to browser environment
- ⚠️ Accuracy varies by browser

**Languages:** English (India), Hindi, English (US)

**Setup:** No configuration required

### 2. Google Cloud Speech

**Features:**
- ✅ High accuracy
- ✅ Wide language support
- ✅ Server-side processing
- ⚠️ Requires Google Cloud account
- ⚠️ Usage-based pricing

**Languages:** 100+ languages including all major Indian languages

**Setup:**
```bash
# Set environment variables
export USE_GOOGLE_CLOUD_SPEECH=True
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 3. AI4Bharat

**Features:**
- ✅ Optimized for Indian languages
- ✅ Server-side processing
- ✅ Better accuracy for regional languages
- ⚠️ Requires AI4Bharat API key
- ⚠️ Limited to Indian languages

**Languages:** Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, English

---

## AI4Bharat Integration

### Step 1: Get API Key

1. Visit [AI4Bharat website](https://ai4bharat.org/)
2. Sign up for an account
3. Navigate to API section
4. Generate an API key

### Step 2: Configure Environment

Add to your `.env` file:

```bash
# AI4Bharat Configuration
AI4BHARAT_API_KEY=your_api_key_here
AI4BHARAT_DEFAULT_LANGUAGE=hi  # Hindi by default
AI4BHARAT_VOICE_GENDER=female
AI4BHARAT_SPEAKING_RATE=1.0
```

### Step 3: Update Settings

Add to `config/settings.py`:

```python
# AI4Bharat Voice Service Configuration
AI4BHARAT_API_KEY = os.getenv('AI4BHARAT_API_KEY', '')
AI4BHARAT_ASR_ENDPOINT = os.getenv('AI4BHARAT_ASR_ENDPOINT',
                                    'https://api.ai4bharat.org/asr/v1/recognize')
AI4BHARAT_TTS_ENDPOINT = os.getenv('AI4BHARAT_TTS_ENDPOINT',
                                    'https://api.ai4bharat.org/tts/v1/synthesize')
```

### Step 4: Test the Integration

```bash
# Start Django server
python manage.py runserver

# Test API endpoint
curl -X POST http://localhost:8000/voicebot/api/voice-provider/test/ \
  -H "Content-Type: application/json" \
  -d '{"provider": "ai4bharat"}'
```

### Step 5: Use in Frontend

```javascript
// Set AI4Bharat as provider
fetch('/voicebot/api/voice-provider/config/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider: 'ai4bharat' })
});
```

---

## Asterisk Telephony Integration

### Overview

Asterisk integration allows your voicebot to handle actual phone calls, providing voice-based appointment booking over the phone.

### Prerequisites

- Asterisk PBX server (version 18+)
- Asterisk REST Interface (ARI) enabled
- Network connectivity between Django server and Asterisk

### Step 1: Install Asterisk

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install asterisk

# CentOS/RHEL
sudo yum install asterisk

# Start Asterisk
sudo systemctl start asterisk
sudo systemctl enable asterisk
```

### Step 2: Configure Asterisk ARI

Edit `/etc/asterisk/ari.conf`:

```ini
[general]
enabled = yes
pretty = yes

[voicebot]
type = user
read_only = no
password = your_secure_password_here
```

Edit `/etc/asterisk/http.conf`:

```ini
[general]
enabled = yes
bindaddr = 0.0.0.0
bindport = 8088
```

Restart Asterisk:

```bash
sudo asterisk -rx "core reload"
```

### Step 3: Configure Django

Add to your `.env` file:

```bash
# Asterisk Configuration
ASTERISK_ENABLED=True
ASTERISK_ARI_URL=http://localhost:8088/ari
ASTERISK_ARI_USERNAME=voicebot
ASTERISK_ARI_PASSWORD=your_secure_password_here
ASTERISK_ARI_APP=voicebot

# Asterisk File Paths
ASTERISK_RECORDING_PATH=/var/spool/asterisk/recording
ASTERISK_AUDIO_PATH=/var/lib/asterisk/sounds/custom
```

### Step 4: Create Asterisk Dialplan

Edit `/etc/asterisk/extensions.conf`:

```ini
[incoming]
; Incoming call from external line
exten => 100,1,Answer()
  same => n,Stasis(voicebot,incoming)
  same => n,Hangup()

[outbound]
; Outbound call initiated by voicebot
exten => _X.,1,Dial(PJSIP/${EXTEN})
  same => n,Hangup()
```

### Step 5: Test Asterisk Integration

```bash
# Test incoming call endpoint
curl -X POST http://localhost:8000/voicebot/api/asterisk/incoming/ \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "test-channel-123",
    "caller_id": "9876543210"
  }'

# Check active calls
curl http://localhost:8000/voicebot/api/asterisk/active-calls/
```

### Step 6: Configure Voicebot with AI4Bharat for Phone Calls

For phone calls, you should use AI4Bharat or Google Cloud (not browser API):

```bash
# In .env
VOICE_PROVIDER=ai4bharat
ASTERISK_ENABLED=True
AI4BHARAT_API_KEY=your_key_here
```

---

## Configuration Guide

### Environment Variables

Complete list of environment variables:

```bash
# Voice Provider Selection
VOICE_PROVIDER=browser  # Options: browser, google, ai4bharat

# Google Cloud Speech
USE_GOOGLE_CLOUD_SPEECH=False
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# AI4Bharat
AI4BHARAT_API_KEY=
AI4BHARAT_ASR_ENDPOINT=https://api.ai4bharat.org/asr/v1/recognize
AI4BHARAT_TTS_ENDPOINT=https://api.ai4bharat.org/tts/v1/synthesize
AI4BHARAT_DEFAULT_LANGUAGE=hi
AI4BHARAT_VOICE_GENDER=female
AI4BHARAT_SPEAKING_RATE=1.0

# Asterisk Telephony
ASTERISK_ENABLED=False
ASTERISK_ARI_URL=http://localhost:8088/ari
ASTERISK_ARI_USERNAME=asterisk
ASTERISK_ARI_PASSWORD=asterisk
ASTERISK_ARI_APP=voicebot
ASTERISK_RECORDING_PATH=/var/spool/asterisk/recording
ASTERISK_AUDIO_PATH=/var/lib/asterisk/sounds/custom
```

### Django Settings

In `config/settings.py`:

```python
# Voice Settings
VOICE_LANGUAGE_DEFAULT = 'en-IN'
VOICE_SUPPORTED_LANGUAGES = ['en-IN', 'hi-IN', 'en-US']
VOICE_SPEAKING_RATE = 0.95
VOICE_ENABLE_AUTO_SPEAK = False

# Voice Provider (override with session preference)
VOICE_PROVIDER = os.getenv('VOICE_PROVIDER', 'browser')
```

---

## API Endpoints

### Voice Provider Endpoints

#### Get Voice Provider Configuration

```http
GET /voicebot/api/voice-provider/config/
```

Response:
```json
{
  "current_provider": "browser",
  "available_providers": [
    {
      "id": "browser",
      "name": "Browser Speech API",
      "description": "Built-in browser speech recognition (Free)",
      "languages": ["en-IN", "hi-IN", "en-US"],
      "enabled": true
    },
    {
      "id": "ai4bharat",
      "name": "AI4Bharat",
      "description": "Indian language AI models for speech",
      "languages": ["hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "pa", "en"],
      "enabled": true
    }
  ],
  "asterisk_enabled": false
}
```

#### Set Voice Provider

```http
POST /voicebot/api/voice-provider/config/
Content-Type: application/json

{
  "provider": "ai4bharat"
}
```

#### Test Voice Provider

```http
POST /voicebot/api/voice-provider/test/
Content-Type: application/json

{
  "provider": "ai4bharat"
}
```

### AI4Bharat Endpoints

#### Speech-to-Text

```http
POST /voicebot/api/ai4bharat/stt/
Content-Type: multipart/form-data

audio: <audio_file>
language: hi
```

Response:
```json
{
  "success": true,
  "transcript": "मुझे डॉक्टर से अपॉइंटमेंट बुक करना है",
  "confidence": 0.95,
  "language": "hi"
}
```

#### Text-to-Speech

```http
POST /voicebot/api/ai4bharat/tts/
Content-Type: application/json

{
  "text": "आपका अपॉइंटमेंट बुक हो गया है",
  "language": "hi",
  "voice_gender": "female"
}
```

Response: Audio file (WAV format)

#### Get Supported Languages

```http
GET /voicebot/api/ai4bharat/languages/
```

### Asterisk Endpoints

#### Incoming Call

```http
POST /voicebot/api/asterisk/incoming/
Content-Type: application/json

{
  "channel_id": "1234567890.123",
  "caller_id": "9876543210"
}
```

#### Process Audio from Call

```http
POST /voicebot/api/asterisk/process/
Content-Type: multipart/form-data

session_id: asterisk_9876543210_1234567890
audio: <audio_file>
language: hi
voice_provider: ai4bharat
session_data: {"stage": "greeting"}
```

#### Make Outbound Call

```http
POST /voicebot/api/asterisk/outbound/
Content-Type: application/json

{
  "phone_number": "9876543210",
  "message": "Your appointment is confirmed"
}
```

#### Get Active Calls

```http
GET /voicebot/api/asterisk/active-calls/
```

#### End Call

```http
POST /voicebot/api/asterisk/end-call/
Content-Type: application/json

{
  "session_id": "asterisk_9876543210_1234567890"
}
```

---

## Frontend Usage

### Opening Voice Settings

Click the "Settings" button (⚙️) in the voicebot interface to open the settings modal.

### Selecting Voice Provider

1. Open Settings modal
2. Choose from dropdown:
   - Browser Speech API (default)
   - Google Cloud Speech
   - AI4Bharat
3. Select language
4. Test connection (optional)
5. Save settings

### JavaScript Integration

```javascript
// Load voice settings
async function loadVoiceSettings() {
    const response = await fetch('/voicebot/api/voice-provider/config/');
    const data = await response.json();
    console.log('Current provider:', data.current_provider);
}

// Change provider
async function changeProvider(provider) {
    const response = await fetch('/voicebot/api/voice-provider/config/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: provider })
    });

    if (response.ok) {
        console.log('Provider changed successfully');
    }
}

// Test provider
async function testProvider(provider) {
    const response = await fetch('/voicebot/api/voice-provider/test/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: provider })
    });

    const result = await response.json();
    console.log('Test result:', result);
}
```

---

## Troubleshooting

### AI4Bharat Issues

**Problem:** API returns 401 Unauthorized

**Solution:**
```bash
# Check API key is set
echo $AI4BHARAT_API_KEY

# Verify in Django shell
python manage.py shell
>>> from django.conf import settings
>>> settings.AI4BHARAT_API_KEY
```

**Problem:** No audio generated from TTS

**Solution:**
- Check audio format is supported (WAV recommended)
- Verify language code is correct
- Test with simple text first

### Asterisk Issues

**Problem:** Cannot connect to ARI

**Solution:**
```bash
# Check Asterisk is running
sudo systemctl status asterisk

# Test ARI directly
curl -u voicebot:password http://localhost:8088/ari/channels

# Check ARI configuration
sudo asterisk -rx "ari show status"
```

**Problem:** Audio quality issues

**Solution:**
```ini
# In /etc/asterisk/rtp.conf
[general]
rtpstart=10000
rtpend=20000
strictrtp=yes
```

**Problem:** Calls not reaching voicebot

**Solution:**
- Verify dialplan configuration
- Check Stasis application name matches
- Review Asterisk logs: `/var/log/asterisk/full`

### General Issues

**Problem:** Settings not saving

**Solution:**
- Check browser console for errors
- Verify CSRF token is included
- Check Django logs for backend errors

**Problem:** Language not changing

**Solution:**
```javascript
// Clear session storage
sessionStorage.clear();

// Reload page
location.reload();
```

---

## Production Deployment

### Security Considerations

1. **API Keys:**
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly

2. **Asterisk:**
   - Use strong passwords for ARI
   - Enable TLS/SSL for ARI connections
   - Restrict ARI access by IP

3. **Network:**
   - Use firewall rules to restrict access
   - Enable HTTPS for Django
   - Use VPN for Asterisk-Django communication

### Performance Optimization

1. **Caching:**
   ```python
   # Cache voice provider settings
   from django.core.cache import cache

   provider = cache.get('voice_provider')
   if not provider:
       provider = get_voice_provider()
       cache.set('voice_provider', provider, 3600)
   ```

2. **Connection Pooling:**
   ```python
   # Reuse HTTP connections
   session = requests.Session()
   ```

3. **Audio Compression:**
   - Use Opus codec for Asterisk
   - Compress audio before sending to APIs

### Monitoring

```python
# Add logging
import logging
logger = logging.getLogger(__name__)

logger.info(f"Voice provider: {provider}")
logger.error(f"STT failed: {error}")
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/vishnuam155-creator/claud-appoimnet/issues
- AI4Bharat Support: https://ai4bharat.org/support
- Asterisk Community: https://community.asterisk.org/

---

## License

This integration is part of the MediBot Voice Assistant project.
