"""
Views for handling WhatsApp webhook and web interface
"""
import uuid
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.utils import timezone

from .models import WhatsAppMessage, WhatsAppSession
from .whatsapp_service import whatsapp_service
from chatbot.conversation_manager import ConversationManager


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_webhook(request):
    """
    Webhook endpoint to receive incoming WhatsApp messages from Twilio

    Twilio sends POST requests to this endpoint when messages are received
    """
    try:
        # Parse Twilio webhook data
        from_number = request.POST.get('From', '')  # Format: whatsapp:+1234567890
        to_number = request.POST.get('To', '')
        message_body = request.POST.get('Body', '').strip()
        message_sid = request.POST.get('MessageSid', '')
        media_url = request.POST.get('MediaUrl0', None)

        # Extract phone number without 'whatsapp:' prefix
        phone_number = from_number.replace('whatsapp:', '')

        # Get or create session
        session, created = WhatsAppSession.objects.get_or_create(
            phone_number=phone_number,
            is_active=True,
            defaults={'session_id': str(uuid.uuid4())}
        )
        session.last_message_at = timezone.now()
        session.save()

        # Log incoming message
        WhatsAppMessage.objects.create(
            message_sid=message_sid,
            from_number=phone_number,
            to_number=to_number.replace('whatsapp:', ''),
            body=message_body,
            direction='inbound',
            session_id=session.session_id,
            media_url=media_url
        )

        # Process message through chatbot
        conversation_manager = ConversationManager()
        response = conversation_manager.process_message(
            message=message_body,
            session_id=session.session_id
        )

        # Format response message
        response_message = response['message']

        # Add options if available
        if response.get('options'):
            options_text = "\n\n" + "\n".join([
                f"{i+1}. {opt['label']}"
                for i, opt in enumerate(response['options'])
            ])
            response_message += options_text + "\n\nReply with the number of your choice."

        # Send response back via WhatsApp
        result = whatsapp_service.send_message(from_number, response_message)

        # Log outbound message
        if result:
            WhatsAppMessage.objects.create(
                message_sid=result.get('sid'),
                from_number=to_number.replace('whatsapp:', ''),
                to_number=phone_number,
                body=response_message,
                direction='outbound',
                session_id=session.session_id,
                status=result.get('status')
            )

        # Link appointment if booking is completed
        if response.get('booking_id') and not session.appointment:
            from appointments.models import Appointment
            try:
                appointment = Appointment.objects.get(booking_id=response['booking_id'])
                session.appointment = appointment
                session.save()
            except Appointment.DoesNotExist:
                pass

        # Return empty response (Twilio expects 200 OK)
        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        return HttpResponse(status=500)


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_status_webhook(request):
    """
    Webhook endpoint to receive message status updates from Twilio
    """
    try:
        message_sid = request.POST.get('MessageSid', '')
        message_status = request.POST.get('MessageStatus', '')

        # Update message status
        WhatsAppMessage.objects.filter(message_sid=message_sid).update(
            status=message_status
        )

        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error processing status webhook: {str(e)}")
        return HttpResponse(status=500)


def whatsapp_chat_interface(request):
    """
    Render WhatsApp-like chat interface for web users
    """
    context = {
        'page_title': 'WhatsApp Chat - Book Appointment'
    }
    return render(request, 'whatsapp_integration/whatsapp_chat.html', context)


def whatsapp_admin_dashboard(request):
    """
    Admin dashboard to view WhatsApp conversations
    """
    # Get recent sessions
    sessions = WhatsAppSession.objects.select_related('appointment').all()[:50]

    context = {
        'sessions': sessions,
        'page_title': 'WhatsApp Conversations'
    }
    return render(request, 'whatsapp_integration/admin_dashboard.html', context)


@require_http_methods(["GET"])
def session_messages(request, session_id):
    """
    API endpoint to get all messages for a session
    """
    messages = WhatsAppMessage.objects.filter(session_id=session_id).order_by('timestamp')

    data = [{
        'id': msg.id,
        'from_number': msg.from_number,
        'to_number': msg.to_number,
        'body': msg.body,
        'direction': msg.direction,
        'timestamp': msg.timestamp.isoformat(),
        'status': msg.status
    } for msg in messages]

    return JsonResponse({'messages': data})
