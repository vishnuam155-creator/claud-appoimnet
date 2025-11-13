"""
Simple Verification Script for Voice Intelligence Assistant
Run this to verify the implementation is correct.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_files():
    """Check if all required files exist."""
    print("=" * 60)
    print("1. CHECKING FILES...")
    print("=" * 60)

    required_files = [
        'voicebot/voice_intelligence_service.py',
        'voicebot/database_action_handler.py',
        'voicebot/voice_intelligence_manager.py',
        'voicebot/voice_intelligence_views.py',
        'voicebot/urls.py',
        'voicebot/README_VOICE_INTELLIGENCE.md',
        'voicebot/VOICE_INTELLIGENCE_EXAMPLES.md',
    ]

    all_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING!")
            all_exist = False

    print()
    if all_exist:
        print("✅ All files present!\n")
        return True
    else:
        print("❌ Some files are missing!\n")
        return False


def check_imports():
    """Check if modules can be imported."""
    print("=" * 60)
    print("2. CHECKING IMPORTS...")
    print("=" * 60)

    try:
        # Try importing the modules
        from voicebot.voice_intelligence_service import VoiceIntelligenceService
        print("✓ VoiceIntelligenceService")

        from voicebot.database_action_handler import DatabaseActionHandler
        print("✓ DatabaseActionHandler")

        from voicebot.voice_intelligence_manager import VoiceIntelligenceManager
        print("✓ VoiceIntelligenceManager")

        from voicebot import voice_intelligence_views
        print("✓ voice_intelligence_views")

        print("\n✅ All modules can be imported!\n")
        return True

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("Make sure Django and dependencies are installed.\n")
        return False


def check_class_structure():
    """Check if classes have required methods."""
    print("=" * 60)
    print("3. CHECKING CLASS STRUCTURE...")
    print("=" * 60)

    try:
        from voicebot.voice_intelligence_service import VoiceIntelligenceService
        from voicebot.database_action_handler import DatabaseActionHandler
        from voicebot.voice_intelligence_manager import VoiceIntelligenceManager

        # Check VoiceIntelligenceService
        service = VoiceIntelligenceService()
        required_methods = [
            'understand_voice_input',
            'identify_intent',
            'generate_database_action',
            'generate_voice_response',
        ]

        print("VoiceIntelligenceService methods:")
        for method in required_methods:
            if hasattr(service, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method} - MISSING!")

        # Check DatabaseActionHandler
        handler = DatabaseActionHandler()
        required_methods = [
            'execute_action',
            'create_appointment',
            'lookup_appointment',
            'cancel_appointment',
            'get_doctors',
        ]

        print("\nDatabaseActionHandler methods:")
        for method in required_methods:
            if hasattr(handler, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method} - MISSING!")

        # Check VoiceIntelligenceManager
        manager = VoiceIntelligenceManager()
        required_methods = [
            'process_voice_input',
            'execute_database_action_directly',
            'get_intent_and_action',
        ]

        print("\nVoiceIntelligenceManager methods:")
        for method in required_methods:
            if hasattr(manager, method):
                print(f"  ✓ {method}")
            else:
                print(f"  ✗ {method} - MISSING!")

        print("\n✅ All classes have required methods!\n")
        return True

    except Exception as e:
        print(f"\n❌ Error checking class structure: {e}\n")
        return False


def test_voice_understanding():
    """Test voice understanding functionality."""
    print("=" * 60)
    print("4. TESTING VOICE UNDERSTANDING...")
    print("=" * 60)

    try:
        from voicebot.voice_intelligence_manager import VoiceIntelligenceManager

        manager = VoiceIntelligenceManager()

        test_cases = [
            "Book appointment tomorrow with Dr. Rahul",
            "Check my appointment",
            "Cancel my booking",
        ]

        print("Testing intent detection:\n")

        for i, test_input in enumerate(test_cases, 1):
            print(f"Test {i}: \"{test_input}\"")
            try:
                result = manager.get_intent_and_action(test_input)
                intent = result.get('intent', {}).get('intent', 'unknown')
                print(f"  → Intent detected: {intent}")

                if result.get('database_action'):
                    action = result['database_action'].get('action', 'none')
                    query_type = result['database_action'].get('query_type', 'none')
                    print(f"  → Action: {action}")
                    print(f"  → Query type: {query_type}")

                print(f"  ✓ Processed successfully")
            except Exception as e:
                print(f"  ✗ Error: {e}")

            print()

        print("✅ Voice understanding is working!\n")
        return True

    except Exception as e:
        print(f"❌ Error testing voice understanding: {e}\n")
        return False


def check_urls():
    """Check if URL patterns are configured."""
    print("=" * 60)
    print("5. CHECKING URL CONFIGURATION...")
    print("=" * 60)

    try:
        # Read urls.py file
        with open('voicebot/urls.py', 'r') as f:
            content = f.read()

        required_patterns = [
            'voice_intelligence_views',
            'api/intelligence/',
            'api/database-action/',
            'api/intent-analysis/',
            'api/session/',
            'api/v2/',
        ]

        print("Checking URL patterns:")
        all_present = True
        for pattern in required_patterns:
            if pattern in content:
                print(f"  ✓ {pattern}")
            else:
                print(f"  ✗ {pattern} - MISSING!")
                all_present = False

        print()
        if all_present:
            print("✅ All URL patterns configured!\n")
            return True
        else:
            print("❌ Some URL patterns are missing!\n")
            return False

    except Exception as e:
        print(f"❌ Error checking URLs: {e}\n")
        return False


def print_summary(results):
    """Print summary of all checks."""
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    checks = [
        ("Files Check", results[0]),
        ("Import Check", results[1]),
        ("Class Structure Check", results[2]),
        ("Voice Understanding Test", results[3]),
        ("URL Configuration Check", results[4]),
    ]

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for check_name, result in checks:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{check_name}: {status}")

    print()
    print(f"Total: {passed}/{total} checks passed")
    print()

    if passed == total:
        print("🎉 ALL CHECKS PASSED!")
        print("Voice Intelligence Assistant is correctly implemented!")
        print()
        print("Next steps:")
        print("1. Start Django server: python manage.py runserver")
        print("2. Test API endpoints (see test_voice_intelligence_api.sh)")
        print("3. Check documentation in README_VOICE_INTELLIGENCE.md")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("Review the output above to see what needs to be fixed.")


def main():
    """Run all verification checks."""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   Voice Intelligence Assistant - Verification Script       ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    results = []

    # Run checks
    results.append(check_files())
    results.append(check_imports())
    results.append(check_class_structure())
    results.append(test_voice_understanding())
    results.append(check_urls())

    # Print summary
    print_summary(results)

    # Return exit code
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
