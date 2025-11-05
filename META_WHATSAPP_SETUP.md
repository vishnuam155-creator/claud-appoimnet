# Meta WhatsApp Business API Setup Guide

This application now uses **Meta WhatsApp Business API** directly instead of Twilio.

## Prerequisites

1. A Meta Business Account
2. A WhatsApp Business Account
3. A verified WhatsApp Business phone number

## Setup Steps

### 1. Create Meta Developer Account

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a developer account or log in
3. Create a new App and select "Business" as the app type

### 2. Add WhatsApp Product

1. In your Meta App dashboard, click "Add Product"
2. Select "WhatsApp" and click "Set Up"
3. Follow the setup wizard to configure your WhatsApp Business Account

### 3. Get API Credentials

You'll need the following credentials:

#### Access Token
1. Go to WhatsApp > API Setup
2. Create a permanent access token (recommended for production)
3. Copy the access token

#### Phone Number ID
1. In WhatsApp > API Setup, you'll see "Phone Number ID"
2. Copy this ID

#### Business Account ID
1. Find this in your Business Settings
2. Copy the Business Account ID

### 4. Configure Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# Meta WhatsApp Business API Configuration
META_WHATSAPP_TOKEN=your-permanent-access-token-here
META_WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id-here
META_WEBHOOK_VERIFY_TOKEN=your-custom-verify-token-here
META_BUSINESS_ACCOUNT_ID=your-business-account-id-here

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# AI API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**Note:** The `META_WEBHOOK_VERIFY_TOKEN` is a custom string you create. You'll use this when setting up the webhook in Meta.

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Setup Webhook in Meta

1. Go to WhatsApp > Configuration in your Meta App
2. Click "Edit" on Webhook
3. Enter your webhook URL: `https://your-domain.com/whatsapp/webhook/`
4. Enter the verify token you set in `META_WEBHOOK_VERIFY_TOKEN`
5. Click "Verify and Save"

**Important:** Your server must be publicly accessible with HTTPS. For local development, use tools like [ngrok](https://ngrok.com/):

```bash
ngrok http 8000
```

Then use the ngrok URL as your webhook URL.

### 7. Subscribe to Webhook Events

After verifying the webhook, subscribe to these fields:
- `messages` - To receive incoming messages
- `message_status` - To receive message delivery status

### 8. Test Phone Numbers (Development)

During development, you can add test phone numbers:
1. Go to WhatsApp > API Setup
2. Under "Send and receive messages", click "Add phone number"
3. Add phone numbers you want to test with

### 9. Go Live (Production)

To use the API in production:
1. Complete Meta Business verification
2. Get your WhatsApp Business Account approved
3. Verify your business phone number
4. Request production access

## API Features

### Text Messages
```python
whatsapp_service.send_message('+1234567890', 'Hello from Meta WhatsApp API!')
```

### Interactive Buttons
```python
whatsapp_service.send_interactive_buttons(
    '+1234567890',
    'Choose an option:',
    [
        {'id': 'opt1', 'title': 'Option 1'},
        {'id': 'opt2', 'title': 'Option 2'},
        {'id': 'opt3', 'title': 'Option 3'}
    ]
)
```

## Webhook Format

### Incoming Message Example
```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "metadata": {
          "display_phone_number": "PHONE_NUMBER",
          "phone_number_id": "PHONE_NUMBER_ID"
        },
        "messages": [{
          "from": "SENDER_PHONE_NUMBER",
          "id": "MESSAGE_ID",
          "timestamp": "TIMESTAMP",
          "type": "text",
          "text": {
            "body": "MESSAGE_CONTENT"
          }
        }]
      }
    }]
  }]
}
```

## Rate Limits

- **Tier 1 (Default)**: 1,000 business-initiated conversations per day
- **Tier 2**: 10,000 conversations per day
- **Tier 3**: 100,000 conversations per day
- **Tier 4**: Unlimited

Tiers are upgraded automatically based on your message quality rating and volume.

## Pricing

Meta WhatsApp Business API uses conversation-based pricing:
- **Business-initiated conversations**: When you send the first message
- **User-initiated conversations**: When the user messages you first (free for 24 hours)

Check [Meta's pricing page](https://developers.facebook.com/docs/whatsapp/pricing) for current rates.

## Resources

- [Meta WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Cloud API Quick Start](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhook Reference](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)

## Troubleshooting

### Webhook verification fails
- Ensure your `META_WEBHOOK_VERIFY_TOKEN` matches what you entered in Meta
- Check that your server is accessible via HTTPS
- Verify the webhook URL is correct

### Messages not sending
- Check your access token is valid
- Verify the phone number ID is correct
- Ensure the recipient's phone number is in the correct format (without '+')
- Check rate limits

### Messages not receiving
- Verify webhook is subscribed to 'messages' field
- Check webhook endpoint is returning 200 status
- Review server logs for errors

## Support

For issues specific to Meta WhatsApp API, refer to:
- [Meta Developer Support](https://developers.facebook.com/support/)
- [WhatsApp Business API Documentation](https://developers.facebook.com/docs/whatsapp)
