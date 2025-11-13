#!/bin/bash
# Test Script for Voice Intelligence Assistant
# This script tests all API endpoints to verify the implementation

echo "================================================"
echo "Voice Intelligence Assistant - API Test Suite"
echo "================================================"
echo ""

# Configuration
BASE_URL="http://localhost:8000/voicebot"
SESSION_ID=""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to test an endpoint
test_endpoint() {
    local test_name="$1"
    local endpoint="$2"
    local data="$3"
    local expected_field="$4"

    echo -e "${YELLOW}Testing: $test_name${NC}"
    echo "Endpoint: POST $endpoint"
    echo "Request data: $data"

    response=$(curl -s -X POST "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data")

    echo "Response: $response"

    # Check if expected field exists in response
    if echo "$response" | grep -q "$expected_field"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 1: Intent Analysis Endpoint (simplest test)
echo "=== Test 1: Intent Analysis ==="
test_endpoint \
    "Intent Analysis - Simple Query" \
    "/api/intent-analysis/" \
    '{"voice_text": "I want to book an appointment"}' \
    "intent"

# Test 2: Intent Analysis - Appointment Lookup
echo "=== Test 2: Intent Analysis - Lookup ==="
test_endpoint \
    "Intent Analysis - Appointment Lookup" \
    "/api/intent-analysis/" \
    '{"voice_text": "Check my appointment with phone 9876543210"}' \
    "appointment_lookup"

# Test 3: Voice Intelligence Endpoint
echo "=== Test 3: Full Voice Intelligence Processing ==="
test_endpoint \
    "Voice Intelligence - Full Processing" \
    "/api/intelligence/" \
    '{"voice_text": "Hello, I need help"}' \
    "voice_response"

# Test 4: Voice Intelligence with Session
echo "=== Test 4: Voice Intelligence with Session ==="
test_endpoint \
    "Voice Intelligence - With Session" \
    "/api/intelligence/" \
    '{"voice_text": "Book appointment tomorrow", "session_id": "test-session-123"}' \
    "session_id"

# Test 5: Database Action - Appointment Lookup (will fail without valid data, but tests endpoint)
echo "=== Test 5: Database Action - Lookup ==="
test_endpoint \
    "Database Action - Appointment Lookup" \
    "/api/database-action/" \
    '{"action": "query_database", "query_type": "appointment_lookup", "parameters": {"phone": "9876543210"}}' \
    "voice_response"

# Test 6: Mixed Language Input
echo "=== Test 6: Mixed Language Support ==="
test_endpoint \
    "Mixed Language - Hindi/English" \
    "/api/intent-analysis/" \
    '{"voice_text": "Kal morning appointment chahiye"}' \
    "intent"

# Test 7: Noisy/Incomplete Input
echo "=== Test 7: Noisy Input Handling ==="
test_endpoint \
    "Noisy Input - Incomplete Speech" \
    "/api/intent-analysis/" \
    '{"voice_text": "um... book... doctor... tomorrow"}' \
    "intent"

# Test 8: Legacy Compatibility Endpoint
echo "=== Test 8: Legacy Compatibility (v2) ==="
test_endpoint \
    "Legacy API v2" \
    "/api/v2/" \
    '{"message": "Hello"}' \
    "message"

# Test 9: Error Handling - Empty Input
echo "=== Test 9: Error Handling - Empty Input ==="
response=$(curl -s -X POST "$BASE_URL/api/intelligence/" \
    -H "Content-Type: application/json" \
    -d '{"voice_text": ""}')

echo "Testing: Error Handling for Empty Input"
echo "Response: $response"

if echo "$response" | grep -q "error\|required"; then
    echo -e "${GREEN}✓ PASSED - Error handled correctly${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED - Error not handled${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 10: Session Management - GET
echo "=== Test 10: Session Management - GET ==="
response=$(curl -s -X GET "$BASE_URL/api/session/?session_id=test-session-123")

echo "Testing: Session Info Retrieval"
echo "Response: $response"

if echo "$response" | grep -q "session_id"; then
    echo -e "${GREEN}✓ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAILED${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Summary
echo ""
echo "================================================"
echo "Test Summary"
echo "================================================"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Voice Intelligence Assistant is working correctly.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed. Check the output above for details.${NC}"
    echo "Note: Database action tests may fail if there's no data. This is normal."
    exit 1
fi
