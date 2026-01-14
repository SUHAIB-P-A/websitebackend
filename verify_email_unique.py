import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "websitebackend.settings")
django.setup()

from formapp.models import CollectionForm

email = "test_duplicate@example.com"

# Create first entry
c1 = CollectionForm.objects.create(
    first_name="Test1",
    last_name="User1",
    email=email,
    phone_number="1234567890"
)
print(f"Created first user with email {email}")

# Create second entry
try:
    c2 = CollectionForm.objects.create(
        first_name="Test2",
        last_name="User2",
        email=email,
        phone_number="0987654321"
    )
    print(f"Created second user with email {email} - SUCCESS")
except Exception as e:
    print(f"Failed to create second user: {e}")

# Cleanup
c1.delete()
try:
    c2.delete()
except:
    pass
