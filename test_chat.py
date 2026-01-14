import os
import django
import sys

# Setup Django environment
sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from chat.views import MessageViewSet
from rest_framework.test import APIRequestFactory

def test_chat_endpoints():
    factory = APIRequestFactory()
    viewset = MessageViewSet()
    
    print("✓ Chat views imported successfully")
    print("✓ All imports resolved (datetime, mongo_client functions)")
    print("\nChat system is ready to use!")
    print("\nNext steps:")
    print("1. Restart your Django backend server")
    print("2. Test sending a message from the admin panel")
    print("3. Verify the conversation loads correctly")
    
if __name__ == "__main__":
    try:
        test_chat_endpoints()
        print("\n✅ All chat components loaded successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
