import anthropic
from django.conf import settings  # or use os.environ

def test_claude_api_key():
    try:
        client = anthropic.Anthropic(api_key="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")
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Claude API key is valid'"}]
        )

        print("✅ Claude API key works!")
        print("Response:", response.content[0].text)

    except anthropic.APIError as e:
        print("❌ Claude API Error:", e)
    except Exception as e:
        print("❌ Invalid Claude API Key or connection issue:", e)


# Run the test
test_claude_api_key()
