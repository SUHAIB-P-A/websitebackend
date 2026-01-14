import os
import django
import sys
from datetime import datetime

sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from chat.mongo_client import messages_collection, save_message, get_conversation

def test_conversation_query():
    # Test: Create sample messages and verify the query
    print("=== Testing Conversation Query Logic ===\n")
    
    # Count existing messages
    total = messages_collection.count_documents({})
    print(f"Total messages in DB: {total}\n")
    
    # Test conversation between user 1 and user 2
    user1_id = 1
    user2_id = 2
    
    # Check all messages between these users (ignoring deleted flags)
    all_msgs_query = {
        '$or': [
            {'sender_id': user1_id, 'receiver_id': user2_id},
            {'sender_id': user2_id, 'receiver_id': user1_id}
        ]
    }
    all_count = messages_collection.count_documents(all_msgs_query)
    print(f"All messages between user {user1_id} and {user2_id}: {all_count}")
    
    # Check with deleted flags
    filtered_msgs = get_conversation(user1_id, user2_id)
    print(f"Filtered messages (deleted flags applied): {len(filtered_msgs)}")
    
    # Show deleted flag statistics
    deleted_by_sender_count = messages_collection.count_documents({
        '$or': [
            {'sender_id': user1_id, 'receiver_id': user2_id, 'deleted_by_sender': True}
        ]
    })
    
    deleted_by_receiver_count = messages_collection.count_documents({
        '$or': [
            {'sender_id': user2_id, 'receiver_id': user1_id, 'deleted_by_receiver': True}
        ]
    })
    
    print(f"\nMessages marked deleted_by_sender: {deleted_by_sender_count}")
    print(f"Messages marked deleted_by_receiver: {deleted_by_receiver_count}")
    
    # Show sample of messages
    print(f"\n=== Sample Messages ===")
    for msg in messages_collection.find(all_msgs_query).limit(5):
        print(f"ID: {msg['_id']}, From: {msg['sender_id']} -> To: {msg['receiver_id']}")
        print(f"  Content: {msg['content'][:50]}...")
        print(f"  Deleted by sender: {msg.get('deleted_by_sender', False)}")
        print(f"  Deleted by receiver: {msg.get('deleted_by_receiver', False)}")
        print()

if __name__ == "__main__":
    test_conversation_query()
