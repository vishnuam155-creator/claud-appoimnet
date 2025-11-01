# Intelligent Medical Appointment Booking Bot

## Overview
This booking bot now features **advanced AI-powered intelligence** that can understand patient intent, handle corrections naturally, and provide a conversational booking experience.

---

## Key Intelligent Features

### 1. **Intent Detection System**
The bot now uses Google Gemini AI to detect what the patient really wants to do, even when they change their mind.

**Supported Intents:**
- `proceed` - Continue with the booking normally
- `change_doctor` - Patient wants to select a different doctor
- `change_date` - Patient wants to change the appointment date
- `change_time` - Patient wants to change the appointment time
- `go_back` - Patient wants to go back to a previous step
- `clarify` - Patient needs help or clarification
- `cancel` - Patient wants to cancel the booking

---

### 2. **Natural Language Corrections**

The bot understands when patients change their mind using natural phrases:

#### Examples:

**Changing Doctor:**
```
Patient: "I selected Dr. Smith but actually I want Dr. Johnson"
Bot: [Detects change_doctor intent]
     "No problem! Let me help you select a different doctor."
     [Shows doctor list again]
```

**Changing Date:**
```
Patient: "Wait, I can't make it on Monday. Can I change to Tuesday?"
Bot: [Detects change_date intent]
     "Of course! Let's pick a different date."
     [Shows date options again]
```

**Changing Time:**
```
Patient: "Actually, I prefer a different time slot"
Bot: [Detects change_time intent]
     "Sure! Here are the other available time slots."
     [Shows time options again]
```

**Going Back:**
```
Patient: "Can we go back? I want to change the doctor"
Bot: [Detects go_back intent]
     "Of course! Going back to doctor selection."
     [Returns to doctor selection stage]
```

---

### 3. **Context-Aware Responses**

The bot remembers your entire conversation and booking context:
- Previous selections (doctor, date, time)
- Symptoms mentioned
- Conversation history
- Current booking stage

This allows the bot to:
- Reference past choices
- Suggest alternatives based on context
- Provide personalized responses
- Handle complex multi-step changes

---

### 4. **Flexible Booking Flow**

**Before (Rigid):**
- Linear flow only
- No going back
- Couldn't change selections
- Start over if mistake

**Now (Flexible):**
- Change any selection anytime
- Go back to previous steps
- Context preserved during changes
- Natural conversation flow

---

### 5. **Smart Conversation Handling**

The bot now detects:

**Trigger Phrases for Changes:**
- "actually", "wait", "no", "change", "different", "instead"
- "wrong", "not that one", "other option", "prefer"
- "go back", "previous", "earlier step"
- "cancel", "nevermind"

**Example Conversation Flow:**
```
User: "I have back pain"
Bot: "I recommend an Orthopedist. Here are available doctors:"
     [Shows Dr. Smith, Dr. Johnson]

User: "Dr. Smith"
Bot: "Great! When would you like to schedule?"
     [Shows dates]

User: "Next Monday"
Bot: "Perfect! Here are available times for Monday:"
     [Shows times: 10:00 AM, 2:00 PM, 4:00 PM]

User: "2:00 PM"
Bot: "Excellent! What's your name?"

User: "Wait, actually can I change the time to 4:00 PM?"
Bot: [INTELLIGENTLY DETECTS: change_time intent]
     "Of course! Let me update that for you."
     [Changes time to 4:00 PM]
     "Your appointment is now scheduled for Monday at 4:00 PM."
     "What's your name?"
```

---

## Technical Implementation

### Files Modified:

#### 1. `chatbot/claude_service.py`
**New Methods:**
- `detect_intent(user_message, current_stage, context)` - Analyzes user intent using AI
- `generate_contextual_response(message, intent, stage, context)` - Generates empathetic responses based on detected intent

**How it works:**
```python
# Example intent detection
intent = claude.detect_intent(
    "Actually I want a different doctor",
    current_stage="date_selection",
    context={'doctor_name': 'Dr. Smith', 'symptoms': 'back pain'}
)

# Returns:
{
    "intent": "change_doctor",
    "confidence": "high",
    "extracted_value": null,
    "reasoning": "User said 'actually' and 'different doctor' indicating desire to change doctor selection"
}
```

#### 2. `chatbot/conversation_manager.py`
**Enhanced Methods:**
- `process_message()` - Now includes intent detection before processing
- New change handlers:
  - `_handle_change_doctor()`
  - `_handle_change_date()`
  - `_handle_change_time()`
  - `_handle_go_back()`
  - `_handle_cancel()`
  - `_handle_clarification()`

**Flow:**
```
User Message → Intent Detection → Route to Handler → Generate Response
```

---

## Usage Examples

### Example 1: Simple Booking (No Changes)
```
User: "I have a headache"
Bot: "I recommend seeing a General Physician..."
User: "Dr. Smith"
Bot: "When would you like to schedule?"
User: "Tomorrow"
Bot: "Available times: 10:00 AM, 2:00 PM..."
User: "10:00 AM"
Bot: "What's your name?"
User: "John Doe"
Bot: "Phone number?"
User: "555-1234"
Bot: ✅ Appointment Confirmed!
```

### Example 2: Booking with Corrections
```
User: "I have a fever and cough"
Bot: "I recommend a General Physician..."
User: "Dr. Johnson"
Bot: "When would you like to schedule?"
User: "Next Monday"
Bot: "Available times: 9:00 AM, 11:00 AM, 2:00 PM..."
User: "2:00 PM"
Bot: "What's your name?"
User: "Wait, can I change the time to 11:00 AM?"
Bot: [DETECTS: change_time] "Of course! Updating your time..."
     "Available times again:"
User: "11:00 AM"
Bot: "Perfect! Now scheduled for Monday at 11:00 AM."
     "What's your name?"
User: "Sarah Williams"
Bot: "Phone number?"
User: "555-5678"
Bot: ✅ Appointment Confirmed!
```

### Example 3: Multiple Changes
```
User: "Back pain"
Bot: "I recommend an Orthopedist. Here are the doctors..."
User: "Dr. Anderson"
Bot: "When would you like to schedule?"
User: "Wednesday"
Bot: "Available times: 1:00 PM, 3:00 PM, 5:00 PM..."
User: "Actually, I want to see Dr. Martinez instead"
Bot: [DETECTS: change_doctor] "No problem! Here are the doctors again..."
User: "Dr. Martinez"
Bot: "When would you like to schedule?"
User: "Friday"
Bot: "Available times: 10:00 AM, 12:00 PM, 4:00 PM..."
User: "10:00 AM"
Bot: "What's your name?"
User: "Michael Chen"
Bot: ✅ Appointment Confirmed with Dr. Martinez on Friday at 10:00 AM!
```

---

## Benefits

### For Patients:
✅ Natural conversation - talk like you would to a person
✅ Fix mistakes easily - change your mind anytime
✅ No need to start over - make corrections in-flow
✅ Clear communication - bot understands intent
✅ Flexible scheduling - adjust date/time as needed

### For Healthcare Providers:
✅ Reduced booking errors - patients can self-correct
✅ Higher completion rates - less frustration
✅ Better patient experience - conversational interface
✅ Complete booking data - context preserved
✅ Conversation history - audit trail maintained

---

## AI Technology Used

**Model:** Google Gemini 2.5 Flash
**Purpose:** Intent detection & contextual response generation

**Why Gemini?**
- Fast response times (< 2 seconds)
- Excellent natural language understanding
- JSON structured outputs
- Cost-effective for high-volume conversations

---

## Configuration

The intelligent bot is automatically enabled. No additional configuration needed!

**API Key:** Set in `config/settings.py`
```python
ANTHROPIC_API_KEY = "your-google-gemini-api-key"
```

**Session Timeout:** 1 hour (conversation state preserved)
**Cache:** Django default cache (in-memory)

---

## Debugging

To see intent detection in action, check your console logs:

```
[Intent Detection] Stage: date_selection, Intent: change_doctor, Confidence: high
[Intent Detection] Stage: time_selection, Intent: change_time, Confidence: high
```

---

## Future Enhancements

Planned features:
- Multi-language support
- Voice input/output
- Smart rescheduling based on calendar conflicts
- Appointment reminders via SMS
- Integration with electronic health records (EHR)

---

## Support

For issues or questions:
1. Check conversation logs
2. Review intent detection output
3. Verify Gemini API key is valid
4. Ensure `google-generativeai` package is installed

---

**Built with ❤️ using Google Gemini AI**
