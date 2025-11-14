"""
API Documentation Endpoint
Provides comprehensive information about all available REST API endpoints
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def api_documentation(request):
    """
    Comprehensive API documentation endpoint
    Returns information about all available REST API endpoints
    """

    api_docs = {
        "success": True,
        "api_version": "1.0",
        "description": "Medical Appointment Booking System REST API",
        "base_url": request.build_absolute_uri('/'),
        "endpoints": {
            "patient_booking": {
                "description": "Patient booking and chatbot APIs",
                "base_path": "/api/",
                "endpoints": [
                    {
                        "path": "/api/chatbot/",
                        "methods": ["GET", "POST"],
                        "description": "Chatbot conversation endpoint",
                        "POST": {
                            "required_fields": ["message"],
                            "optional_fields": ["session_id"],
                            "response": {
                                "success": "boolean",
                                "session_id": "string",
                                "message": "string",
                                "action": "string",
                                "options": "array",
                                "booking_id": "string"
                            }
                        }
                    },
                    {
                        "path": "/api/voice/",
                        "methods": ["GET", "POST"],
                        "description": "Voice transcription and synthesis API",
                        "POST": {
                            "actions": ["transcribe", "synthesize", "voice_guidance"],
                            "transcribe": {
                                "required_fields": ["action=transcribe", "audio_data (base64)", "audio_format"],
                            },
                            "synthesize": {
                                "required_fields": ["action=synthesize", "text"],
                                "optional_fields": ["language"]
                            }
                        }
                    },
                    {
                        "path": "/api/voice-assistant/",
                        "methods": ["GET", "POST"],
                        "description": "Voice assistant conversation endpoint",
                        "POST": {
                            "required_fields": ["message"],
                            "optional_fields": ["session_id", "session_data"],
                            "response": {
                                "success": "boolean",
                                "session_id": "string",
                                "message": "string",
                                "stage": "string",
                                "action": "string",
                                "data": "object"
                            }
                        }
                    }
                ]
            },
            "admin_panel": {
                "description": "Admin panel APIs for managing appointments",
                "base_path": "/admin-panel/api/",
                "authentication": "Required: Staff/Admin user",
                "endpoints": [
                    {
                        "path": "/admin-panel/api/dashboard/",
                        "methods": ["GET"],
                        "description": "Get dashboard statistics",
                        "response": {
                            "statistics": "object with counts",
                            "upcoming_appointments": "array",
                            "recent_appointments": "array",
                            "status_breakdown": "array"
                        }
                    },
                    {
                        "path": "/admin-panel/api/appointments/",
                        "methods": ["GET"],
                        "description": "List appointments with filters and pagination",
                        "query_params": {
                            "status": "Filter by status (pending, confirmed, cancelled, completed, no_show)",
                            "doctor": "Filter by doctor ID",
                            "date": "Filter by date (YYYY-MM-DD)",
                            "search": "Search by patient name, phone, or booking ID",
                            "page": "Page number (default: 1)",
                            "page_size": "Items per page (default: 20)"
                        },
                        "response": {
                            "success": "boolean",
                            "count": "number - total count",
                            "page": "number",
                            "page_size": "number",
                            "total_pages": "number",
                            "appointments": "array of appointment objects"
                        }
                    },
                    {
                        "path": "/admin-panel/api/appointments/{booking_id}/",
                        "methods": ["GET"],
                        "description": "Get detailed appointment information",
                        "response": {
                            "success": "boolean",
                            "appointment": "detailed appointment object with history and SMS notifications"
                        }
                    },
                    {
                        "path": "/admin-panel/api/appointments/{booking_id}/update/",
                        "methods": ["PUT", "PATCH"],
                        "description": "Update appointment status",
                        "required_fields": ["status"],
                        "optional_fields": ["notes", "changed_by"],
                        "status_choices": ["pending", "confirmed", "cancelled", "completed", "no_show"],
                        "response": {
                            "success": "boolean",
                            "message": "string",
                            "appointment": "updated appointment object"
                        }
                    },
                    {
                        "path": "/admin-panel/api/calendar/",
                        "methods": ["GET"],
                        "description": "Get calendar data for a specific month",
                        "query_params": {
                            "year": "Year (default: current year)",
                            "month": "Month 1-12 (default: current month)"
                        },
                        "response": {
                            "year": "number",
                            "month": "number",
                            "month_name": "string",
                            "calendar_weeks": "array of weeks",
                            "appointments_by_date": "object with appointments grouped by date"
                        }
                    },
                    {
                        "path": "/admin-panel/api/appointments-by-date/",
                        "methods": ["GET"],
                        "description": "Get all appointments for a specific date",
                        "query_params": {
                            "date": "Date in YYYY-MM-DD format (required)"
                        },
                        "response": {
                            "success": "boolean",
                            "date": "string",
                            "count": "number",
                            "appointments": "array of appointments"
                        }
                    }
                ]
            },
            "voicebot": {
                "description": "Advanced voice intelligence APIs",
                "base_path": "/voicebot/api/",
                "endpoints": [
                    {
                        "path": "/voicebot/api/intelligence/",
                        "methods": ["POST"],
                        "description": "Main voice intelligence endpoint for processing voice input"
                    },
                    {
                        "path": "/voicebot/api/database-action/",
                        "methods": ["POST"],
                        "description": "Execute database actions based on intents"
                    },
                    {
                        "path": "/voicebot/api/intent-analysis/",
                        "methods": ["POST"],
                        "description": "Analyze user intent without execution"
                    },
                    {
                        "path": "/voicebot/api/session/",
                        "methods": ["GET", "DELETE"],
                        "description": "Manage voice assistant sessions"
                    }
                ]
            },
            "whatsapp": {
                "description": "WhatsApp integration APIs",
                "base_path": "/whatsapp/",
                "endpoints": [
                    {
                        "path": "/whatsapp/webhook/",
                        "methods": ["GET", "POST"],
                        "description": "WhatsApp webhook for incoming messages (Meta)",
                        "GET": "Webhook verification",
                        "POST": "Receive incoming messages"
                    },
                    {
                        "path": "/whatsapp/webhook/status/",
                        "methods": ["POST"],
                        "description": "WhatsApp message status updates webhook"
                    },
                    {
                        "path": "/whatsapp/api/sessions/",
                        "methods": ["GET"],
                        "description": "Get all WhatsApp conversation sessions",
                        "query_params": {
                            "is_active": "Filter by active status (true/false)",
                            "phone_number": "Filter by phone number",
                            "page": "Page number (default: 1)",
                            "page_size": "Items per page (default: 50)"
                        }
                    },
                    {
                        "path": "/whatsapp/api/sessions/{session_id}/messages/",
                        "methods": ["GET"],
                        "description": "Get all messages for a specific session"
                    }
                ]
            }
        },
        "data_models": {
            "Appointment": {
                "fields": [
                    "id", "doctor", "patient_name", "patient_phone", "patient_email",
                    "patient_age", "patient_gender", "appointment_date", "appointment_time",
                    "symptoms", "notes", "status", "booking_id", "session_id",
                    "created_at", "updated_at"
                ],
                "status_choices": ["pending", "confirmed", "cancelled", "completed", "no_show"]
            },
            "Doctor": {
                "fields": [
                    "id", "name", "specialization", "phone", "email",
                    "qualification", "experience_years", "consultation_fee",
                    "is_active", "photo", "bio"
                ]
            },
            "Specialization": {
                "fields": ["id", "name", "description", "keywords"]
            }
        },
        "authentication": {
            "admin_endpoints": "Require admin/staff authentication",
            "public_endpoints": "Chatbot, Voice, WhatsApp webhooks",
            "note": "CSRF exempt for all API endpoints"
        },
        "response_format": {
            "success_response": {
                "success": True,
                "data": "..."
            },
            "error_response": {
                "success": False,
                "error": "error message"
            }
        }
    }

    return JsonResponse(api_docs, json_dumps_params={'indent': 2})


@require_http_methods(["GET"])
def api_health_check(request):
    """
    Simple health check endpoint
    """
    return JsonResponse({
        "success": True,
        "status": "healthy",
        "message": "Medical Appointment Booking API is running"
    })
