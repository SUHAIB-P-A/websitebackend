
import os
import django
import sys
import json

# Setup Django environment
sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff
from rest_framework.test import APIRequestFactory
from formapp.views import staff_login, staff_detail

def verify_admin_persistence():
    print("--- Starting Verification ---")
    
    # 1. Cleanup: Ensure clean state for 'admin' (optional, but good for test isolation)
    # But here we want to test if the VIEW creates it. So let's delete if exists.
    try:
        Staff.objects.get(login_id='admin').delete()
        print("Deleted existing admin for clean test.")
    except Staff.DoesNotExist:
        print("No existing admin found. Proceeding.")

    factory = APIRequestFactory()

    # 2. Simulate Login (First time - should create admin)
    print("\n[Step 1] Attempting First Login with 'admin'/'admin123'...")
    request = factory.post('/api/staff-login/', {'login_id': 'admin', 'password': 'admin123'}, format='json')
    response = staff_login(request)
    
    if response.status_code != 200:
        print(f"FAILED: Login failed with status {response.status_code}")
        print(response.data)
        return

    data = response.data
    staff_id = data.get('staff_id')
    print(f"SUCCESS: Login successful. Created Staff ID: {staff_id}")
    
    if staff_id is None:
        print("FAILED: staff_id is None! Admin was not created in DB.")
        return

    # 3. Verify DB Record exists
    try:
        admin_staff = Staff.objects.get(id=staff_id)
        print(f"VERIFIED: Database record found for {admin_staff.name} (Role: {admin_staff.role})")
    except Staff.DoesNotExist:
        print("FAILED: Database record NOT found after login!")
        return

    # 4. Simulate Profile Update (Change Name)
    print("\n[Step 2] Updating Admin Profile (Name -> 'Super Admin')...")
    request_update = factory.put(f'/api/staff/{staff_id}/', {'name': 'Super Admin'}, format='json')
    response_update = staff_detail(request_update, pk=staff_id)
    
    if response_update.status_code != 200:
        print(f"FAILED: Update failed with status {response_update.status_code}")
        return
    
    print("SUCCESS: Update request successful.")

    # 5. Verify Persistence by Re-fetching from DB
    admin_staff.refresh_from_db()
    if admin_staff.name == 'Super Admin':
        print(f"VERIFIED: Name persisted in DB as '{admin_staff.name}'")
    else:
        print(f"FAILED: Name did not persist! Current DB Name: '{admin_staff.name}'")
        return

    # 6. Verify Persistence via Login
    print("\n[Step 3] Re-logging in to verify returned data...")
    request_relogin = factory.post('/api/staff-login/', {'login_id': 'admin', 'password': 'admin123'}, format='json')
    response_relogin = staff_login(request_relogin)
    
    relogin_data = response_relogin.data
    if relogin_data.get('name') == 'Super Admin':
        print(f"VERIFIED: Re-login returned updated name: '{relogin_data.get('name')}'")
    else:
        print(f"FAILED: Re-login returned old name: '{relogin_data.get('name')}'")

if __name__ == '__main__':
    verify_admin_persistence()
