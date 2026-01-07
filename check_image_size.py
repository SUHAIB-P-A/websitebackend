
import os
import django
import sys

sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff

try:
    admin = Staff.objects.get(id=9)
    img_len = len(admin.profile_image) if admin.profile_image else 0
    print(f"Admin (ID 9) Profile Image Length: {img_len} chars")
    print(f"Approx Size: {img_len / 1024 / 1024:.2f} MB")
except Staff.DoesNotExist:
    print("User ID 9 not found.")
