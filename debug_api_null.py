import requests
import json

url = "http://127.0.0.1:8000/api/submit/"

# Test with course_selected as None (null)
payload = {
    "first_name": "TestNull",
    "last_name": "User",
    "email": "testnull@example.com",
    "phone_number": "1234567899",
    "plus_two_percentage": "85.50",
    "city": "Test City",
    "course_selected": None,
    "colleges_selected": "Test College"
}

try:
    print("Testing with course_selected=None...")
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

# Test with course_selected as empty string
payload2 = {
    "first_name": "TestEmpty",
    "last_name": "User",
    "email": "testempty@example.com",
    "phone_number": "1234567898",
    "plus_two_percentage": "85.50",
    "city": "Test City",
    "course_selected": "",
    "colleges_selected": "Test College"
}

try:
    print("\nTesting with course_selected=''...")
    response = requests.post(url, json=payload2)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
