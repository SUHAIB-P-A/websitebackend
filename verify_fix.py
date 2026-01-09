import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "websitebackend.settings")
django.setup()

from formapp.models import Staff
from rest_framework.test import APIRequestFactory
from formapp.views import staff_login

def test_admin_creation():
    print("Testing Admin Auto-Creation...")

    # 1. Ensure Admin does NOT exist
    existing_admin = Staff.objects.filter(login_id='admin').first()
    if existing_admin:
        print(f"Admin already exists (ID: {existing_admin.id}). Deleting for clean test...")
        existing_admin.delete()
    
    # 2. Simulate Login
    factory = APIRequestFactory()
    login_payload = {
        "login_id": "admin",
        "password": "admin123"
    }
    request = factory.post('/api/login/', login_payload, format='json')
    response = staff_login(request)

    # 3. Verify Response
    print(f"Login Response: {response.status_code}")
    print(f"Response Data: {response.data}")

    if response.status_code == 200:
        if response.data.get('staff_id') is not None:
             print("SUCCESS: valid staff_id returned.")
        else:
             print("FAILURE: staff_id is still None.")
    else:
        print("FAILURE: Login failed.")

    # 4. Verify DB Record
    new_admin = Staff.objects.filter(login_id='admin').first()
    if new_admin:
        print(f"SUCCESS: Admin record found in DB (ID: {new_admin.id}).")
    else:
        print("FAILURE: Admin record NOT found in DB.")

if __name__ == "__main__":
    test_admin_creation()
