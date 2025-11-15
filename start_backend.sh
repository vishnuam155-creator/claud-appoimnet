#!/bin/bash

# Start Backend Server Script
# Medical Appointment Booking System

echo "================================================"
echo "  Starting Medical Appointment Backend Server"
echo "================================================"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Found virtual environment (venv)"
    source venv/bin/activate
elif [ -d "env" ]; then
    echo "✓ Found virtual environment (env)"
    source env/bin/activate
else
    echo "⚠ No virtual environment found. Using system Python."
fi

echo ""
echo "Checking database migrations..."
python manage.py migrate --noinput

echo ""
echo "================================================"
echo "  Backend Server Starting..."
echo "================================================"
echo ""
echo "  Base URL: http://127.0.0.1:8000"
echo "  API Docs: http://127.0.0.1:8000/api/docs/"
echo "  Health Check: http://127.0.0.1:8000/api/health/"
echo ""
echo "  Your frontend at http://localhost:8080 can now connect!"
echo ""
echo "================================================"
echo ""

# Start Django development server
python manage.py runserver 8000
