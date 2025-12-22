import requests
import json

url = "http://127.0.0.1:8000/api/submit/"

payload = {
    "first_name": "Test",
    "last_name": "User",
    "email": "testuser@example.com",
    "phone_number": "1234567890",
    "plus_two_percentage": "85.50",
    "city": "Test City",
    "course_selected": "Test Course",
    "colleges_selected": "Test College"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
