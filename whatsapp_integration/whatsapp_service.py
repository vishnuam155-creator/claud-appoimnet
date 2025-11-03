"""
WhatsApp Service for sending and receiving messages via Twilio
"""
import os
from typing import Dict, Optional, List
from django.conf import settings


class WhatsAppService:
    """Service to handle WhatsApp message sending through Twilio"""

    def __init__(self):
        # Twilio credentials from environment variables
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # Twilio sandbox number

        # Initialize Twilio client if credentials are available
        self.client = None
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
            except ImportError:
                print("Warning: Twilio package not installed. Install with: pip install twilio")

    def send_message(self, to_number: str, message: str) -> Optional[Dict]:
        """
        Send a WhatsApp message to a phone number

        Args:
            to_number: Phone number in format +1234567890
            message: Message text to send

        Returns:
            Dict with message details or None if failed
        """
        if not self.client:
            print("Twilio client not initialized. Check credentials.")
            return None

        try:
            # Ensure number is in WhatsApp format
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'

            # Send message
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=to_number
            )

            return {
                'sid': twilio_message.sid,
                'status': twilio_message.status,
                'to': to_number,
                'body': message
            }

        except Exception as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return None

    def send_message_with_options(self, to_number: str, message: str, options: List[Dict]) -> Optional[Dict]:
        """
        Send a WhatsApp message with interactive options

        Args:
            to_number: Phone number
            message: Message text
            options: List of option dictionaries with 'label' and 'value'

        Returns:
            Dict with message details or None if failed
        """
        # Format options as numbered list
        if options:
            options_text = "\n\n" + "\n".join([
                f"{i+1}. {opt['label']}" for i, opt in enumerate(options)
            ])
            full_message = message + options_text + "\n\nReply with the number of your choice."
        else:
            full_message = message

        return self.send_message(to_number, full_message)

    def format_confirmation_message(self, booking_details: Dict) -> str:
        """
        Format booking confirmation message

        Args:
            booking_details: Dictionary containing booking information

        Returns:
            Formatted confirmation message
        """
        return f"""
 *Appointment Confirmed!*

=Ë Booking ID: {booking_details.get('booking_id', 'N/A')}

=d Patient: {booking_details.get('patient_name', 'N/A')}
=h• Doctor: {booking_details.get('doctor_name', 'N/A')}
<å Department: {booking_details.get('specialization', 'N/A')}

=Å Date: {booking_details.get('date', 'N/A')}
=R Time: {booking_details.get('time', 'N/A')}

=Í Clinic Address: [Your clinic address here]

*Please arrive 10 minutes before your appointment time.*

For any queries, contact us at [clinic phone number]
""".strip()

    def validate_phone_number(self, phone: str) -> str:
        """
        Validate and format phone number

        Args:
            phone: Phone number string

        Returns:
            Formatted phone number with country code
        """
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone))

        # Add country code if missing (assuming India +91)
        if len(cleaned) == 10:
            cleaned = '91' + cleaned

        # Add + prefix
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned

        return cleaned


# Singleton instance
whatsapp_service = WhatsAppService()
