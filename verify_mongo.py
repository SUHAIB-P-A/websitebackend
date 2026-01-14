import os
import django
import sys
from datetime import datetime

# Setup Django environment
sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from chat.mongo_client import messages_collection, save_message

def test_mongo():
    print("Testing MongoDB Connection...")
    try:
        # 1. Test Insert
        test_data = {
            'sender_id': 99999, # Test ID
            'receiver_id': 88888, # Test ID
            'content': 'Test message from verification script'
        }
        print(f"Attempting to insert: {test_data}")
        start_time = datetime.now()
        
        saved_msg = save_message(test_data)
        
        print(f"Success! Inserted document ID: {saved_msg['id']}")
        print(f"Time taken: {datetime.now() - start_time}")

        # 2. Test Fetch
        print("Attempting to fetch the inserted document...")
        from bson.objectid import ObjectId
        fetched_doc = messages_collection.find_one({'_id': ObjectId(saved_msg['id'])})
        
        if fetched_doc:
            print(f"Success! Fetched document: {fetched_doc}")
            
            # 3. Clean up
            print("Cleaning up test document...")
            messages_collection.delete_one({'_id': ObjectId(saved_msg['id'])})
            print("Deleted test document.")
            return True
        else:
            print("Failed to fetch the document immediately after insert.")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_mongo():
        print("\n✅ MongoDB Connection & Write/Read Verified Successfully!")
    else:
        print("\n❌ MongoDB Verification Failed.")
