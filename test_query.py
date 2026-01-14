import os
import django
import sys

sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from chat.mongo_client import messages_collection, get_conversation

# Test with actual user IDs from the database
user1_id = 23  # The most active sender
user2_id = 1   # The receiver

print(f"=== Testing Conversation Query ===")
print(f"User 1 (Viewer): {user1_id}")
print(f"User 2 (Other): {user2_id}\n")

# Count all messages between these users (no filters)
all_msgs = messages_collection.find({
    '$or': [
        {'sender_id': user1_id, 'receiver_id': user2_id},
        {'sender_id': user2_id, 'receiver_id': user1_id}
    ]
}).sort('timestamp', 1)

all_count = 0
print("=== All Messages (no filtering) === ")
for msg in all_msgs:
    all_count += 1
    print(f"{all_count}. From {msg['sender_id']} -> {msg['receiver_id']}: {msg['content'][:30]}")
    print(f"   deleted_by_sender: {msg.get('deleted_by_sender', False)}, deleted_by_receiver: {msg.get('deleted_by_receiver', False)}")

print(f"\nTotal messages (unfiltered): {all_count}")

# Now test with the query function
filtered_msgs = get_conversation(user1_id, user2_id)
print(f"\nFiltered messages (via get_conversation): {len(filtered_msgs)}")

if all_count != len(filtered_msgs):
    print(f"\n⚠️ MISMATCH: {all_count - len(filtered_msgs)} messages are being filtered out!")
    
    # Find which ones are filtered
    filtered_ids = set(m['id'] for m in filtered_msgs)
    all_ids = list(messages_collection.find({
        '$or': [
            {'sender_id': user1_id, 'receiver_id': user2_id},
            {'sender_id': user2_id, 'receiver_id': user1_id}
        ]
    }))
    
    print("\n=== Messages Being Filtered Out ===")
    for msg in all_ids:
        msg_id = str(msg['_id'])
        if msg_id not in filtered_ids:
            print(f"ID: {msg_id}")
            print(f"  From {msg['sender_id']} -> {msg['receiver_id']}: {msg['content'][:30]}")
            print(f"  deleted_by_sender: {msg.get('deleted_by_sender', False)}")
            print(f"  deleted_by_receiver: {msg.get('deleted_by_receiver', False)}")
            print()
else:
    print("✅ All messages are being returned correctly!")
