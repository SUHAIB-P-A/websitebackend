import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "websitebackend.settings")
django.setup()

from formapp.models import Staff
from rest_framework.test import APIRequestFactory
from formapp.views import staff_detail

def run_tests():
    print("Starting Save Error Reproduction...")

    # Build a factory
    factory = APIRequestFactory()
    
    # 1. Get the admin user (or create if missing)
    try:
        # Try to find 'admin' (or 'superadmin' if I left it like that in verify script)
        # Actually in verify_role_functionality.py I changed it to 'superadmin' but then DID NOT change it back.
        # So likely the user is logged in as 'superadmin' (if they didn't logout) or 'admin' is gone?
        # WAIT. If I changed login_id to 'superadmin', and the user is trying to log in as 'admin', they would hit the "Auto Create" logic again?
        # If they are logged in, who are they?
        
        # Let's check who exists
        print("Existing Staff:")
        for s in Staff.objects.all():
            print(f" - {s.name} (ID: {s.id}, Login: {s.login_id}, Role: {s.role})")
            
        # Pick the first admin
        admin = Staff.objects.filter(role='admin').first()
        if not admin:
            print("No admin found to test with.")
            return

        print(f"\nTesting Update on Admin {admin.login_id} (ID: {admin.id})")
        
        # 2. Simulate Payload from Settings.jsx
        # exact mimic of likely payload
        payload = {
            "name": "New Name Test",
            "phone": "9876543210"
        }
        
        req = factory.put(f'/api/staff/{admin.id}/', payload, format='json')
        resp = staff_detail(req, pk=admin.id)
        
        print(f"\nResponse Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Error Body: {resp.data}")
        else:
            print("Success! (Could not reproduce simple name update failure)")

        # 3. Try duplicate login_id if relevant
        # If we have another user, try to set this admin's login_id to that user's login_id
        other = Staff.objects.exclude(id=admin.id).first()
        if other:
            print(f"\nAttempting to set login_id to existing '{other.login_id}'")
            bad_payload = {"login_id": other.login_id}
            req_bad = factory.put(f'/api/staff/{admin.id}/', bad_payload, format='json')
            resp_bad = staff_detail(req_bad, pk=admin.id)
            print(f"Response Code: {resp_bad.status_code}")
            print(f"Error Body: {resp_bad.data}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    run_tests()
