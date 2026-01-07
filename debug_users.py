
import os
import django
import sys

# Setup Django Environment
sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff

print("--- Staff Users ---")
users = Staff.objects.all()
for u in users:
    print(f"ID: {u.id} | Name: {u.name} | LoginID: {u.login_id} | Active: {u.active_status} | PwdHash: {u.password[:10]}...")

print("\n--- Check exact 'admin' ---")
try:
    admin = Staff.objects.get(login_id__iexact='admin')
    print(f"Found Admin User! ID: {admin.id}")
except Staff.DoesNotExist:
    print("No DB user found with login_id='admin'")
