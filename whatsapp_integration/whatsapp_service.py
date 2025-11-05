"""
WhatsApp Service for sending and receiving messages via Meta WhatsApp Business API
"""
import os
import requests
from typing import Dict, Optional, List
from django.conf import settings


class WhatsAppService:
    """Service to handle WhatsApp message sending through Meta WhatsApp Business API"""

    def __init__(self):
        # Meta WhatsApp Business API credentials from environment variables
        self.access_token = os.getenv('META_WHATSAPP_TOKEN', '')
        self.phone_number_id = os.getenv('META_WHATSAPP_PHONE_NUMBER_ID', '')
        self.verify_token = os.getenv('META_WEBHOOK_VERIFY_TOKEN', '')

        # Meta WhatsApp API endpoint
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"

        # Headers for API requests
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def send_message(self, to_number: str, message: str) -> Optional[Dict]:
        """
        Send a WhatsApp message to a phone number using Meta WhatsApp Business API

        Args:
            to_number: Phone number in format +1234567890 or whatsapp:+1234567890
            message: Message text to send

        Returns:
            Dict with message details or None if failed
        """
        if not self.access_token or not self.phone_number_id:
            print("Meta WhatsApp credentials not configured. Check environment variables.")
            return None

        try:
            # Remove 'whatsapp:' prefix if present
            if to_number.startswith('whatsapp:'):
                to_number = to_number.replace('whatsapp:', '')

            # Remove '+' from phone number for Meta API
            clean_number = to_number.replace('+', '')

            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_number,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message
                }
            }

            # Send message via Meta WhatsApp API
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'sid': result.get('messages', [{}])[0].get('id', ''),
                    'status': 'sent',
                    'to': to_number,
                    'body': message
                }
            else:
                print(f"Error sending WhatsApp message: {response.status_code} - {response.text}")
                return None

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

    def send_interactive_buttons(self, to_number: str, message: str, buttons: List[Dict]) -> Optional[Dict]:
        """
        Send a WhatsApp message with interactive buttons (Meta API feature)

        Args:
            to_number: Phone number
            message: Message text
            buttons: List of button dictionaries with 'id' and 'title' (max 3 buttons)

        Returns:
            Dict with message details or None if failed
        """
        if not self.access_token or not self.phone_number_id:
            print("Meta WhatsApp credentials not configured.")
            return None

        try:
            # Remove 'whatsapp:' prefix if present
            if to_number.startswith('whatsapp:'):
                to_number = to_number.replace('whatsapp:', '')

            clean_number = to_number.replace('+', '')

            # Prepare interactive button message (max 3 buttons)
            button_list = []
            for i, btn in enumerate(buttons[:3]):  # Meta allows max 3 buttons
                button_list.append({
                    "type": "reply",
                    "reply": {
                        "id": btn.get('id', f'btn_{i}'),
                        "title": btn.get('title', '')[:20]  # Max 20 chars
                    }
                })

            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": message
                    },
                    "action": {
                        "buttons": button_list
                    }
                }
            }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'sid': result.get('messages', [{}])[0].get('id', ''),
                    'status': 'sent',
                    'to': to_number,
                    'body': message
                }
            else:
                print(f"Error sending interactive message: {response.status_code} - {response.text}")
                # Fallback to text message
                return self.send_message(to_number, message)

        except Exception as e:
            print(f"Error sending interactive message: {str(e)}")
            return None

    def send_interactive_list(self, to_number: str, header: str, body: str, button_text: str, sections: List[Dict]) -> Optional[Dict]:
        """
        Send a WhatsApp message with interactive list (Meta API feature)

        Args:
            to_number: Phone number
            header: Header text (optional)
            body: Body text
            button_text: Text for the list button (e.g., "Select Option")
            sections: List of sections, each with 'title' and 'rows' (list of items with 'id', 'title', 'description')

        Returns:
            Dict with message details or None if failed
        """
        if not self.access_token or not self.phone_number_id:
            print("Meta WhatsApp credentials not configured.")
            return None

        try:
            # Remove 'whatsapp:' prefix if present
            if to_number.startswith('whatsapp:'):
                to_number = to_number.replace('whatsapp:', '')

            clean_number = to_number.replace('+', '')

            # Prepare interactive list message
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_number,
                "type": "interactive",
                "interactive": {
                    "type": "list",
                    "body": {
                        "text": body
                    },
                    "action": {
                        "button": button_text[:20],  # Max 20 chars
                        "sections": sections
                    }
                }
            }

            # Add header if provided
            if header:
                payload["interactive"]["header"] = {
                    "type": "text",
                    "text": header[:60]  # Max 60 chars
                }

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'sid': result.get('messages', [{}])[0].get('id', ''),
                    'status': 'sent',
                    'to': to_number,
                    'body': body
                }
            else:
                print(f"Error sending interactive list: {response.status_code} - {response.text}")
                # Fallback to text message with numbered options
                return self.send_message(to_number, body)

        except Exception as e:
            print(f"Error sending interactive list: {str(e)}")
            return None

    def format_confirmation_message(self, booking_details: Dict) -> str:
        """
        Format booking confirmation message

        Args:
            booking_details: Dictionary containing booking information

        Returns:
            Formatted confirmation message
        """
        return f"""
✅ *Appointment Confirmed!*

📋 Booking ID: {booking_details.get('booking_id', 'N/A')}

👤 Patient: {booking_details.get('patient_name', 'N/A')}
👨‍⚕️ Doctor: {booking_details.get('doctor_name', 'N/A')}
🏥 Department: {booking_details.get('specialization', 'N/A')}

📅 Date: {booking_details.get('date', 'N/A')}
🕒 Time: {booking_details.get('time', 'N/A')}

📍 Clinic Address: [Your clinic address here]

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

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription (required by Meta)

        Args:
            mode: Verification mode
            token: Verification token
            challenge: Challenge string to echo back

        Returns:
            Challenge string if verification successful, None otherwise
        """
        if mode == 'subscribe' and token == self.verify_token:
            return challenge
        return None


# Singleton instance
whatsapp_service = WhatsAppService()
