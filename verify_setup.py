#!/usr/bin/env python
"""
Quick fix script to verify and fix template issues
Run this from your project root directory
"""
import os
import sys
from pathlib import Path

def main():
    print("🔍 Checking Django project structure...\n")

    # Get project root
    project_root = Path.cwd()
    print(f"Project root: {project_root}")

    # Check if we're in the right directory
    if not (project_root / 'manage.py').exists():
        print("❌ ERROR: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)

    print("✅ Found manage.py")

    # Check templates directory
    templates_dir = project_root / 'templates'
    if not templates_dir.exists():
        print(f"❌ ERROR: templates directory not found at {templates_dir}")
        print("Creating templates directory...")
        templates_dir.mkdir(exist_ok=True)
    else:
        print(f"✅ Found templates directory: {templates_dir}")

    # Check patient_booking templates
    patient_booking_dir = templates_dir / 'patient_booking'
    if not patient_booking_dir.exists():
        print(f"❌ ERROR: patient_booking templates directory not found")
        print("Creating patient_booking templates directory...")
        patient_booking_dir.mkdir(parents=True, exist_ok=True)
    else:
        print(f"✅ Found patient_booking templates: {patient_booking_dir}")

    # Check specific templates
    required_templates = ['home.html', 'chatbot.html', 'voice_assistant.html']
    for template in required_templates:
        template_path = patient_booking_dir / template
        if template_path.exists():
            print(f"✅ Found {template}")
        else:
            print(f"❌ Missing {template}")

    # Check settings.py
    settings_file = project_root / 'config' / 'settings.py'
    if settings_file.exists():
        print(f"\n✅ Found settings.py")

        # Read and check TEMPLATES configuration
        with open(settings_file, 'r') as f:
            content = f.read()
            if "BASE_DIR / 'templates'" in content or 'BASE_DIR / "templates"' in content:
                print("✅ TEMPLATES DIRS configuration looks correct")
            else:
                print("⚠️  WARNING: TEMPLATES DIRS configuration might need checking")

    # Check Django version
    print("\n📦 Checking dependencies...")
    try:
        import django
        print(f"Django version: {django.get_version()}")

        # Check if version matches requirements
        req_file = project_root / 'requirements.txt'
        if req_file.exists():
            with open(req_file, 'r') as f:
                for line in f:
                    if line.startswith('Django=='):
                        required_version = line.strip().split('==')[1]
                        if required_version != django.get_version():
                            print(f"⚠️  WARNING: Django version mismatch!")
                            print(f"   Required: {required_version}")
                            print(f"   Installed: {django.get_version()}")
                            print(f"   Run: pip install Django=={required_version}")
    except ImportError:
        print("❌ Django not installed. Run: pip install -r requirements.txt")

    print("\n" + "="*60)
    print("SUMMARY & NEXT STEPS:")
    print("="*60)
    print("\n1. If templates are missing, they should be in your git repository.")
    print("   Make sure you cloned/copied the entire project.\n")
    print("2. Ensure all dependencies are installed:")
    print("   pip install -r requirements.txt\n")
    print("3. Run migrations:")
    print("   python manage.py migrate\n")
    print("4. Start the server:")
    print("   python manage.py runserver\n")
    print("5. Visit: http://127.0.0.1:8000/\n")

if __name__ == '__main__':
    main()
