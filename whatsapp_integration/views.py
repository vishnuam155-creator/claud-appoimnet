"""
Views for handling WhatsApp webhook and web interface
"""
import json
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
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """
    Webhook endpoint to receive incoming WhatsApp messages from Meta

    Meta sends GET requests for webhook verification and POST for messages
    """
    # Handle webhook verification (GET request)
    if request.method == 'GET':
        mode = request.GET.get('hub.mode', '')
        token = request.GET.get('hub.verify_token', '')
        challenge = request.GET.get('hub.challenge', '')

        verified_challenge = whatsapp_service.verify_webhook(mode, token, challenge)
        if verified_challenge:
            return HttpResponse(verified_challenge, content_type='text/plain')
        else:
            return HttpResponse('Verification failed', status=403)

    # Handle incoming messages (POST request)
    try:
        # Parse Meta webhook data (JSON format)
        body = json.loads(request.body.decode('utf-8'))

        # Extract message data from Meta webhook structure
        entry = body.get('entry', [])
        if not entry:
            return HttpResponse(status=200)

        changes = entry[0].get('changes', [])
        if not changes:
            return HttpResponse(status=200)

        value = changes[0].get('value', {})
        messages = value.get('messages', [])

        if not messages:
            return HttpResponse(status=200)

        # Process the first message
        message = messages[0]
        message_id = message.get('id', '')
        from_number = message.get('from', '')  # Phone number without prefix
        message_type = message.get('type', 'text')

        # Extract message content based on type
        if message_type == 'text':
            message_body = message.get('text', {}).get('body', '').strip()
        elif message_type == 'interactive':
            # Handle button replies
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                button_reply = interactive.get('button_reply', {})
                message_body = button_reply.get('title', '')
            else:
                message_body = ''
        else:
            message_body = ''

        # Get metadata
        metadata = value.get('metadata', {})
        to_number = metadata.get('display_phone_number', '')

        # Format phone number with + prefix
        phone_number = f'+{from_number}' if not from_number.startswith('+') else from_number

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
            message_sid=message_id,
            from_number=phone_number,
            to_number=to_number,
            body=message_body,
            direction='inbound',
            session_id=session.session_id
        )

        # Process message through chatbot
        conversation_manager = ConversationManager(session.session_id)
        response = conversation_manager.process_message(message_body)

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
        result = whatsapp_service.send_message(phone_number, response_message)

        # Log outbound message
        if result:
            WhatsAppMessage.objects.create(
                message_sid=result.get('sid'),
                from_number=to_number,
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

        # Return empty response (Meta expects 200 OK)
        return HttpResponse(status=200)

    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(status=500)


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_status_webhook(request):
    """
    Webhook endpoint to receive message status updates from Meta
    """
    try:
        # Parse Meta status update (JSON format)
        body = json.loads(request.body.decode('utf-8'))

        entry = body.get('entry', [])
        if not entry:
            return HttpResponse(status=200)

        changes = entry[0].get('changes', [])
        if not changes:
            return HttpResponse(status=200)

        value = changes[0].get('value', {})
        statuses = value.get('statuses', [])

        if not statuses:
            return HttpResponse(status=200)

        # Process status update
        status_update = statuses[0]
        message_id = status_update.get('id', '')
        message_status = status_update.get('status', '')

        # Update message status
        WhatsAppMessage.objects.filter(message_sid=message_id).update(
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
