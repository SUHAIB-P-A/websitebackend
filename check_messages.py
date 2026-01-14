import os
import django
import sys

sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from chat.mongo_client import messages_collection
from datetime import datetime, timedelta

# Check recent messages
print("=== Recent Messages (Last 10) ===\n")
recent_messages = messages_collection.find().sort('timestamp', -1).limit(10)

for i, msg in enumerate(recent_messages, 1):
    print(f"{i}. ID: {msg['_id']}")
    print(f"   From: {msg['sender_id']} -> To: {msg['receiver_id']}")
    print(f"   Content: {msg['content'][:50]}...")
    print(f"   Timestamp: {msg['timestamp']}")
    print(f"   Deleted by sender: {msg.get('deleted_by_sender', False)}")
    print(f"   Deleted by receiver: {msg.get('deleted_by_receiver', False)}")
    print(f"   Is Revoked: {msg.get('is_revoked', False)}")
    print()

# Check if there are messages from last 5 minutes
five_min_ago = datetime.now(tz=None) - timedelta(minutes=5)
recent_count = messages_collection.count_documents({
    'timestamp': {'$gte': five_min_ago}
})
print(f"\n=== Messages in last 5 minutes: {recent_count} ===")

# Count messages by deleted status
total = messages_collection.count_documents({})
deleted_sender = messages_collection.count_documents({'deleted_by_sender': True})
deleted_receiver = messages_collection.count_documents({'deleted_by_receiver': True})
revoked = messages_collection.count_documents({'is_revoked': True})

print(f"\nTotal messages: {total}")
print(f"Marked deleted_by_sender: {deleted_sender}")
print(f"Marked deleted_by_receiver: {deleted_receiver}")
print(f"Revoked messages: {revoked}")
