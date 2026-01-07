
import os
import django
import sys

sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff

try:
    admin = Staff.objects.get(id=9)
    print(f"Checking password 'admin123' for user {admin.name} (ID: 9)...")
    is_valid = admin.check_password('admin123')
    print(f"Is Password Valid? {is_valid}")
except Staff.DoesNotExist:
    print("User ID 9 not found.")
