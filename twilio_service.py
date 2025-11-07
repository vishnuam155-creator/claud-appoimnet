"""
Twilio SMS Service for sending appointment confirmations via SMS.
"""

from django.conf import settings
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging

logger = logging.getLogger(__name__)


def log_sms_notification(appointment, notification_type, phone, message, message_sid, success, error=None):
    """
    Log SMS notification to database.
    Import here to avoid circular dependency.
    """
    try:
        from appointments.models import SMSNotification

        SMSNotification.objects.create(
            appointment=appointment,
            notification_type=notification_type,
            phone_number=phone,
            message_body=message,
            message_sid=message_sid,
            status='sent' if success else 'failed',
            error_message=error
        )
    except Exception as e:
        logger.error(f"Failed to log SMS notification: {str(e)}")


class TwilioSMSService:
    """
    Service class to handle SMS notifications using Twilio API.
    """

    def __init__(self):
        """
        Initialize Twilio client with credentials from settings.
        """
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER

        # Only initialize client if credentials are configured
        if self.account_sid and self.auth_token and self.from_phone:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio SMS service is not configured. SMS notifications will be disabled.")

    def send_sms(self, to_phone, message):
        """
        Send an SMS message to a phone number.

        Args:
            to_phone (str): The recipient's phone number (E.164 format recommended)
            message (str): The SMS message content

        Returns:
            dict: Result dictionary with 'success' (bool), 'message_sid' (str), and 'error' (str) keys
        """
        if not self.enabled:
            logger.warning(f"SMS not sent to {to_phone}: Twilio service is not configured")
            return {
                'success': False,
                'message_sid': None,
                'error': 'Twilio service is not configured'
            }

        # Normalize phone number (add country code if missing)
        normalized_phone = self._normalize_phone_number(to_phone)

        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=normalized_phone
            )

            logger.info(f"SMS sent successfully to {normalized_phone}. SID: {message_obj.sid}")

            return {
                'success': True,
                'message_sid': message_obj.sid,
                'error': None
            }

        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {normalized_phone}: {str(e)}")
            return {
                'success': False,
                'message_sid': None,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {normalized_phone}: {str(e)}")
            return {
                'success': False,
                'message_sid': None,
                'error': str(e)
            }

    def send_appointment_confirmation(self, appointment):
        """
        Send appointment confirmation SMS.

        Args:
            appointment: Appointment model instance

        Returns:
            dict: Result dictionary from send_sms()
        """
        # Format confirmation message
        message = self._format_confirmation_message(appointment)

        # Send SMS to patient's phone
        result = self.send_sms(appointment.patient_phone, message)

        # Log the notification in database
        log_sms_notification(
            appointment=appointment,
            notification_type='confirmation',
            phone=appointment.patient_phone,
            message=message,
            message_sid=result.get('message_sid'),
            success=result.get('success', False),
            error=result.get('error')
        )

        return result

    def _format_confirmation_message(self, appointment):
        """
        Format a confirmation message for an appointment.

        Args:
            appointment: Appointment model instance

        Returns:
            str: Formatted SMS message
        """
        # Format date and time nicely
        date_str = appointment.appointment_date.strftime("%B %d, %Y")
        time_str = appointment.appointment_time.strftime("%I:%M %p")

        message = f"""🏥 Appointment Confirmed!

Hello {appointment.patient_name},

Your appointment has been confirmed:

👨‍⚕️ Doctor: Dr. {appointment.doctor.name}
📅 Date: {date_str}
🕒 Time: {time_str}
🏥 Department: {appointment.doctor.specialization.name}

Booking ID: {appointment.booking_id}

Please arrive 10 minutes early. For any changes, contact the clinic.

Thank you!"""

        return message

    def _normalize_phone_number(self, phone):
        """
        Normalize phone number to E.164 format.
        Assumes Indian phone numbers (+91) if no country code is present.

        Args:
            phone (str): Phone number to normalize

        Returns:
            str: Normalized phone number in E.164 format
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))

        # If it starts with country code (91 for India), add +
        if digits.startswith('91') and len(digits) == 12:
            return f'+{digits}'

        # If it's a 10-digit number, assume India and add +91
        elif len(digits) == 10:
            return f'+91{digits}'

        # If it already has +, return as is
        elif phone.startswith('+'):
            return phone

        # Otherwise, return the original
        else:
            logger.warning(f"Phone number {phone} may not be in correct format")
            return phone

    def send_cancellation_notification(self, appointment):
        """
        Send appointment cancellation SMS.

        Args:
            appointment: Appointment model instance

        Returns:
            dict: Result dictionary from send_sms()
        """
        date_str = appointment.appointment_date.strftime("%B %d, %Y")
        time_str = appointment.appointment_time.strftime("%I:%M %p")

        message = f"""🏥 Appointment Cancelled

Hello {appointment.patient_name},

Your appointment has been cancelled:

Booking ID: {appointment.booking_id}
Date: {date_str}
Time: {time_str}

To reschedule, please contact the clinic or book online.

Thank you!"""

        result = self.send_sms(appointment.patient_phone, message)

        # Log the notification in database
        log_sms_notification(
            appointment=appointment,
            notification_type='cancellation',
            phone=appointment.patient_phone,
            message=message,
            message_sid=result.get('message_sid'),
            success=result.get('success', False),
            error=result.get('error')
        )

        return result

    def send_reschedule_notification(self, appointment, old_date, old_time):
        """
        Send appointment reschedule SMS.

        Args:
            appointment: Appointment model instance (with new date/time)
            old_date: Previous appointment date
            old_time: Previous appointment time

        Returns:
            dict: Result dictionary from send_sms()
        """
        old_date_str = old_date.strftime("%B %d, %Y")
        old_time_str = old_time.strftime("%I:%M %p")
        new_date_str = appointment.appointment_date.strftime("%B %d, %Y")
        new_time_str = appointment.appointment_time.strftime("%I:%M %p")

        message = f"""🏥 Appointment Rescheduled

Hello {appointment.patient_name},

Your appointment has been rescheduled:

Previous:
📅 {old_date_str} at {old_time_str}

New:
📅 {new_date_str} at {new_time_str}

Booking ID: {appointment.booking_id}
Doctor: Dr. {appointment.doctor.name}

Thank you!"""

        result = self.send_sms(appointment.patient_phone, message)

        # Log the notification in database
        log_sms_notification(
            appointment=appointment,
            notification_type='reschedule',
            phone=appointment.patient_phone,
            message=message,
            message_sid=result.get('message_sid'),
            success=result.get('success', False),
            error=result.get('error')
        )

        return result


# Singleton instance
_twilio_service = None


def get_twilio_service():
    """
    Get or create the singleton Twilio service instance.

    Returns:
        TwilioSMSService: The Twilio SMS service instance
    """
    global _twilio_service
    if _twilio_service is None:
        _twilio_service = TwilioSMSService()
    return _twilio_service
