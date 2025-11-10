# Documentation Index

This file helps you navigate all available documentation for the Medical Appointment System.

## Quick Navigation

### Start Here
- **CODEBASE_EXPLORATION.md** - Start with this for a comprehensive overview
- **BOOKING_FLOW_DIAGRAM.md** - Visual diagrams and flow charts
- **KEY_FILES_GUIDE.md** - Quick reference guide for file locations

### Specialized Topics
- **README.md** - Original project README (features, installation, deployment)
- **QUICK_START.md** - Getting started guide
- **TWILIO_SMS_SETUP.md** - SMS configuration guide
- **SMS_FLOW_DIAGRAMS.md** - SMS integration flow diagrams
- **SMS_QUICK_REFERENCE.md** - Quick SMS reference
- **SMS_TWILIO_ANALYSIS.md** - Detailed Twilio analysis
- **WHATSAPP_SETUP.md** - WhatsApp integration guide
- **META_WHATSAPP_SETUP.md** - Meta WhatsApp setup
- **INTELLIGENT_BOT_FEATURES.md** - AI chatbot features

## Document Descriptions

### CODEBASE_EXPLORATION.md (22KB, 652 lines)
**Best for:** Understanding the entire codebase architecture
**Contains:**
- Project overview and features
- Technology stack (Django, Gemini AI, Twilio, etc.)
- Complete project structure
- 7-stage booking flow detailed breakdown
- Patient interactions and forms
- Voice/audio status (currently: NONE)
- Database models and relationships
- AI/LLM integration points (Gemini 2.5-flash)
- Entry points and API routes
- Important files for voice integration
- Configuration and environment variables
- Data flow diagrams
- Summary and key insights

**Read Time:** 30-40 minutes for full understanding

### BOOKING_FLOW_DIAGRAM.md (16KB, 374 lines)
**Best for:** Visual learners, understanding the conversation flow
**Contains:**
- High-level patient journey flow
- 7-stage booking flow (ASCII diagrams)
- Intent detection system (flowchart)
- Database schema relationships (ER diagram)
- AI/LLM integration points
- Chat interface components
- State management structure
- Communication channels
- Key integration points
- Voice integration entry points
- Performance considerations

**Read Time:** 20-30 minutes

### KEY_FILES_GUIDE.md (18KB, 448 lines)
**Best for:** Developers looking for specific code
**Contains:**
- Quick file reference tables
- Complete file structure tree
- Dependency map (import chains)
- Entry points and API endpoints
- Data models summary
- Frontend technologies
- Security and configuration
- Code statistics
- Technology versions
- How to find specific functionality
- File naming conventions

**Read Time:** 15-20 minutes (or use as reference)

## How to Use This Documentation

### I want to understand the appointment booking flow
1. Read: CODEBASE_EXPLORATION.md → Section 4
2. Review: BOOKING_FLOW_DIAGRAM.md → Section 2

### I need to find where specific code is located
1. Use: KEY_FILES_GUIDE.md → Section 7 (How to Find Specific Functionality)
2. Reference: Complete file structure tree

### I want to understand how AI is integrated
1. Read: CODEBASE_EXPLORATION.md → Section 9 (AI/LLM Integration)
2. Review: BOOKING_FLOW_DIAGRAM.md → Section 6 (AI/LLM Integration Points)

### I need to add voice functionality
1. Read: KEY_FILES_GUIDE.md → Section "Next Steps for Voice Integration"
2. Reference: CODEBASE_EXPLORATION.md → Section 11 (Important Files for Voice Integration)
3. Implement: Based on BOOKING_FLOW_DIAGRAM.md → Voice Integration Entry Points

### I want to understand the database structure
1. Review: BOOKING_FLOW_DIAGRAM.md → Section 5 (Database Schema)
2. Details: CODEBASE_EXPLORATION.md → Section 8 (Database Models)

### I need to know about SMS/WhatsApp
1. Read: CODEBASE_EXPLORATION.md → Section 7 (Messaging & Communication)
2. Details: TWILIO_SMS_SETUP.md or WHATSAPP_SETUP.md for implementation

## File Locations

All documentation files are located in: `/home/user/claud-appoimnet/`

Key code files referenced:
- `/home/user/claud-appoimnet/chatbot/conversation_manager.py` (1,384 lines - CORE)
- `/home/user/claud-appoimnet/chatbot/claude_service.py` (246 lines - AI)
- `/home/user/claud-appoimnet/templates/patient_booking/chatbot.html` (382 lines - UI)
- `/home/user/claud-appoimnet/twilio_service.py` (308 lines - SMS)
- `/home/user/claud-appoimnet/patient_booking/views.py` (64 lines - API)

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Documentation | 4,655 lines across 12 files |
| Generated Documentation | 1,474 lines across 3 files |
| Codebase Size | ~2,000+ lines of Python |
| Chat UI Code | ~100 lines of JavaScript |
| Largest Component | whatsapp_service.py (11,110 lines) |
| Core Logic | conversation_manager.py (1,384 lines) |

## Quick Facts

- **Project Type:** Django-based medical appointment booking system
- **AI Model:** Google Gemini 2.5-flash (via google-generativeai)
- **Communication:** Twilio SMS + WhatsApp integration
- **Frontend:** Vanilla JavaScript (no React/Vue)
- **Database:** SQLite (dev), PostgreSQL (recommended for prod)
- **Booking Stages:** 7 (Greeting → Symptoms → Doctor → Date → Time → Details → Confirmation)
- **Voice Status:** 0% implemented, ready for integration

## Next Actions

1. **For Understanding:** Read CODEBASE_EXPLORATION.md
2. **For Visual Understanding:** Review BOOKING_FLOW_DIAGRAM.md
3. **For Code Reference:** Use KEY_FILES_GUIDE.md
4. **For Voice Integration:** See KEY_FILES_GUIDE.md → "Next Steps for Voice Integration"
5. **For SMS Setup:** See TWILIO_SMS_SETUP.md
6. **For WhatsApp:** See WHATSAPP_SETUP.md

---

**Generated:** 2025-11-10  
**Status:** Complete and ready for use  
**Last Updated:** 2025-11-10
