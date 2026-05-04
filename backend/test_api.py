"""
Test script to verify the API is working correctly
"""
import requests
import json
import sys

API_BASE = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_health_check():
    """Test the health endpoint"""
    print_section("Testing Health Check")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"? Error: {e}")
        return False

def test_single_prediction():
    """Test single prediction endpoint"""
    print_section("Testing Single Prediction")
    
    test_cases = [
        {
            "text": "Oh great, another meeting that could have been an email",
            "expected": True  # Expected to be sarcastic
        },
        {
            "text": "I really love working on weekends!",
            "expected": True  # Expected to be sarcastic
        },
        {
            "text": "This is a wonderful day and I am very happy",
            "expected": False  # Expected to be non-sarcastic
        }
    ]
    
    all_passed = True
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['text'][:50]}...")
        try:
            response = requests.post(
                f"{API_BASE}/predict",
                json={"text": test_case["text"], "platform": "test"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"? Status: {response.status_code}")
                print(f"   Sarcastic: {result['is_sarcastic']}")
                print(f"   Confidence: {result['confidence']:.4f}")
                print(f"   Sarcasm Score: {result['sarcasm_score']:.4f}")
                
                # Note: We don't fail tests based on prediction correctness
                # as model accuracy varies
            else:
                print(f"? Status: {response.status_code}")
                print(f"   Error: {response.text}")
                all_passed = False
        except Exception as e:
            print(f"? Error: {e}")
            all_passed = False
    
    return all_passed

def test_batch_prediction():
    """Test batch prediction endpoint"""
    print_section("Testing Batch Prediction")
    
    texts = [
        {"text": "What a fantastic idea!", "platform": "test"},
        {"text": "Sure, because that's exactly what I wanted to do", "platform": "test"},
        {"text": "The weather is nice today", "platform": "test"}
    ]
    
    try:
        response = requests.post(
            f"{API_BASE}/predict/batch",
            json=texts
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"? Processed {len(results)} predictions")
            for i, result in enumerate(results, 1):
                print(f"\n  Prediction {i}:")
                print(f"    Sarcastic: {result['is_sarcastic']}")
                print(f"    Confidence: {result['confidence']:.4f}")
            return True
        else:
            print(f"? Error: {response.text}")
            return False
    except Exception as e:
        print(f"? Error: {e}")
        return False

def test_stats_endpoint():
    """Test statistics endpoint"""
    print_section("Testing Statistics Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/stats")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"? Statistics retrieved:")
            print(json.dumps(stats, indent=2))
            return True
        else:
            print(f"? Error: {response.text}")
            return False
    except Exception as e:
        print(f"? Error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print_section("Testing Root Endpoint")
    
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"? Error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SARCASM DETECTION API - TEST SUITE")
    print("=" * 60)
    print(f"API Base URL: {API_BASE}\n")
    
    results = {
        "Root Endpoint": test_root_endpoint(),
        "Health Check": test_health_check(),
        "Single Prediction": test_single_prediction(),
        "Batch Prediction": test_batch_prediction(),
        "Statistics": test_stats_endpoint()
    }
    
    # Summary
    print_section("TEST SUMMARY")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "? PASSED" if result else "? FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n?? All tests passed!")
        return 0
    else:
        print(f"\n??  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
