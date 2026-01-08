
import os
import django
import requests
import json
import base64

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "websitebackend.settings")
django.setup()

from formapp.models import Staff

def reproduce_api_persistence():
    # 1. Ensure Admin exists
    try:
        admin_user = Staff.objects.get(login_id='admin')
    except Staff.DoesNotExist:
        print("Admin user not found! Create it first.")
        return

    admin_id = admin_user.id
    print(f"Testing with Admin ID: {admin_id}")

    # 2. Prepare Payload (Simulating Settings.jsx)
    new_image_b64 = "data:image/png;base64,UPDATED_IMAGE_DATA_VERIFICATION"
    payload = {
        "name": "Admin API Test",
        "email": "admin_api@example.com",
        "profile_image": new_image_b64
    }
    
    # 3. Use Django Test Client or Requests to hit the API
    from rest_framework.test import APIRequestFactory
    from formapp.views import staff_detail
    
    factory = APIRequestFactory()
    request = factory.put(f'/api/staff/{admin_id}/', payload, format='json')
    
    print("Sending PUT request to update profile...")
    response = staff_detail(request, pk=admin_id)
    
    print(f"Response Status: {response.status_code}")
    if response.status_code == 200:
        print("Response Data:", response.data.get('name'))
        
        # 4. Verify Database Persistence independently
        admin_user.refresh_from_db()
        print(f"DB Image Value: {admin_user.profile_image}")
        
        if admin_user.profile_image == new_image_b64:
            print("SUCCESS: Image persisted in DB!")
        else:
            print("FAILURE: Image NOT updated in DB.")
    else:
        print("API Error:", response.data)

if __name__ == "__main__":
    reproduce_api_persistence()
