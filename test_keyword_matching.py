#!/usr/bin/env python3
"""
Simple unit test for keyword matching logic (no Django/DB required)
"""

class MockSpecialization:
    def __init__(self, name, keywords):
        self.name = name
        self.keywords = keywords

def match_by_keywords(symptoms_text, specializations):
    """
    Match symptoms to specialization using keyword matching
    Returns the best match with a confidence score
    """
    symptoms_lower = symptoms_text.lower()

    # Common medical words that shouldn't be matched in isolation
    common_words = {'pain', 'hurt', 'ache', 'problem', 'issue', 'feel', 'feeling', 'have', 'had', 'get', 'getting'}

    # Score each specialization based on keyword matches
    matches = []
    for spec in specializations:
        if not spec.keywords:
            continue

        keywords = [kw.strip().lower() for kw in spec.keywords.split(',')]
        score = 0
        matched_keywords = []

        for keyword in keywords:
            # Check for exact phrase match (highest priority)
            if keyword in symptoms_lower:
                score += 3  # Higher score for exact match
                matched_keywords.append(keyword)
            else:
                # Check for partial word match (only for meaningful words)
                keyword_words = set(keyword.split())
                symptoms_words = set(symptoms_lower.split())

                # Find matching words that are not common/generic
                meaningful_matches = keyword_words & symptoms_words - common_words

                if meaningful_matches:
                    score += 1  # Lower score for partial match
                    matched_keywords.append(keyword)

        if score > 0:
            matches.append({
                'specialization': spec.name,
                'score': score,
                'matched_keywords': matched_keywords,
                'total_keywords': len(keywords)
            })

    # Sort by score (descending)
    matches.sort(key=lambda x: x['score'], reverse=True)

    if not matches:
        return None

    # Get best match
    best_match = matches[0]

    # Determine confidence based on score
    if best_match['score'] >= 3:
        confidence = 'high'
    elif best_match['score'] >= 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    return {
        'specialization': best_match['specialization'],
        'confidence': confidence,
        'reasoning': f"Matched keywords: {', '.join(best_match['matched_keywords'][:3])}",
        'score': best_match['score']
    }

# Create mock specializations with the same keywords as in your database
specializations = [
    MockSpecialization('Orthopedic', 'leg pain, bone, fracture, joint, back pain, arthritis, knee pain, shoulder pain, spine'),
    MockSpecialization('Cardiologist', 'chest pain, heart, blood pressure, palpitations, cardiovascular, heart attack, cholesterol'),
    MockSpecialization('General Physician', 'fever, cold, flu, general checkup, headache, cough, common ailments, routine checkup'),
    MockSpecialization('Dermatologist', 'skin, rash, acne, hair fall, nail problems, skin infection, allergy'),
    MockSpecialization('Neurologist', 'headache, migraine, dizziness, seizure, stroke, nerve pain, brain')
]

# Test cases
test_cases = [
    {'input': 'I have leg pain', 'expected': 'Orthopedic'},
    {'input': 'My knee hurts', 'expected': 'Orthopedic'},
    {'input': 'I have chest pain', 'expected': 'Cardiologist'},
    {'input': 'I have fever and cold', 'expected': 'General Physician'},
    {'input': 'I have a skin rash', 'expected': 'Dermatologist'},
    {'input': 'I have severe headache', 'expected': 'General Physician'},  # Both Neurologist and General Physician have headache
    {'input': 'My back hurts', 'expected': 'Orthopedic'},
    {'input': 'I have palpitations', 'expected': 'Cardiologist'},
]

print("=" * 70)
print("TESTING KEYWORD MATCHING ALGORITHM")
print("=" * 70)

print("\n📋 Specializations and Keywords:")
print("-" * 70)
for spec in specializations:
    print(f"\n{spec.name}:")
    print(f"  Keywords: {spec.keywords}")

print("\n" + "=" * 70)
print("RUNNING TESTS")
print("=" * 70)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n[Test {i}] Input: \"{test['input']}\"")
    print(f"Expected: {test['expected']}")

    result = match_by_keywords(test['input'], specializations)

    if result:
        print(f"Result: {result['specialization']}")
        print(f"Confidence: {result['confidence']}")
        print(f"Score: {result['score']}")
        print(f"Reasoning: {result['reasoning']}")

        if result['specialization'] == test['expected']:
            print("✅ PASSED")
            passed += 1
        else:
            print(f"❌ FAILED (got {result['specialization']}, expected {test['expected']})")
            failed += 1
    else:
        print("Result: No match found")
        print("❌ FAILED (no match)")
        failed += 1

print("\n" + "=" * 70)
print(f"RESULTS: {passed}/{len(test_cases)} tests passed, {failed} failed")
print("=" * 70)

if failed == 0:
    print("🎉 All tests passed!")
else:
    print(f"⚠️  {failed} test(s) failed.")
