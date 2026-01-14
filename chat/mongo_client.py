from django.conf import settings
from pymongo import MongoClient
import datetime
import certifi

client = MongoClient(settings.MONGO_URI, tlsCAFile=certifi.where())
db = client[settings.MONGO_DB_NAME]
messages_collection = db['messages']

def save_message(data):
    """
    Save a new message to MongoDB.
    data: dict containing sender_id, receiver_id, content
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    message_doc = {
        'sender_id': int(data['sender_id']),
        'receiver_id': int(data['receiver_id']),
        'content': data['content'],
        'timestamp': timestamp,
        'is_read': False,
        'deleted_by_sender': False,
        'deleted_by_receiver': False,
        'is_revoked': False
    }
    result = messages_collection.insert_one(message_doc)
    message_doc['id'] = str(result.inserted_id)
    # Add frontend-compatible field names
    message_doc['sender'] = message_doc['sender_id']
    message_doc['receiver'] = message_doc['receiver_id']
    # Convert timestamp to ISO string for JSON serialization
    message_doc['timestamp'] = timestamp.isoformat()
    # Remove _id as we use id
    if '_id' in message_doc:
        del message_doc['_id']
    return message_doc

def get_conversation(user1_id, user2_id):
    """
    Get messages between two users.
    """
    user1_id = int(user1_id)
    user2_id = int(user2_id)
    
    query = {
        '$or': [
            {
                'sender_id': user1_id, 
                'receiver_id': user2_id, 
                'deleted_by_sender': False
            },
            {
                'sender_id': user2_id, 
                'receiver_id': user1_id, 
                'deleted_by_receiver': False
            }
        ]
    }
    
    # Sort by timestamp ascending
    cursor = messages_collection.find(query).sort('timestamp', 1)
    
    messages = []
    for doc in cursor:
        # Convert _id to string id
        doc['id'] = str(doc['_id'])
        del doc['_id']
        
        # Add frontend-compatible field names (sender/receiver instead of sender_id/receiver_id)
        doc['sender'] = doc['sender_id']
        doc['receiver'] = doc['receiver_id']
        
        # Convert datetime to ISO string for frontend
        if 'timestamp' in doc and isinstance(doc['timestamp'], datetime.datetime):
            doc['timestamp'] = doc['timestamp'].isoformat()
        
        # Handle revoked messages
        if doc.get('is_revoked'):
            if doc['sender_id'] == user1_id:
                doc['content'] = "You deleted this message"
            else:
                doc['content'] = "This message was deleted"
        
        messages.append(doc)
        
    return messages

def get_last_message(user_id, other_user_id):
    """
    Get the last message for user list annotation.
    user_id: The "Viewer"
    other_user_id: The chat partner
    """
    query = {
        '$or': [
            {
                'sender_id': user_id, 
                'receiver_id': other_user_id, 
                'deleted_by_sender': False
            },
            {
                'sender_id': other_user_id, 
                'receiver_id': user_id, 
                'deleted_by_receiver': False
            }
        ]
    }
    
    # Sort desc, limit 1
    doc = messages_collection.find_one(query, sort=[('timestamp', -1)])
    if doc:
        return doc['timestamp']
    return None

def get_unread_count(sender_id, receiver_id):
    """
    Count unread messages sent BY sender TO receiver.
    receiver_id is typically the current user.
    """
    query = {
        'sender_id': int(sender_id),
        'receiver_id': int(receiver_id),
        'is_read': False,
        'deleted_by_receiver': False
    }
    return messages_collection.count_documents(query)

def mark_as_read(sender_id, receiver_id):
    query = {
        'sender_id': int(sender_id),
        'receiver_id': int(receiver_id),
        'is_read': False
    }
    messages_collection.update_many(query, {'$set': {'is_read': True}})

def delete_conversation_local(user_id, target_user_id):
    # Mark messages SENT by user as deleted_by_sender
    messages_collection.update_many(
        {'sender_id': int(user_id), 'receiver_id': int(target_user_id)},
        {'$set': {'deleted_by_sender': True}}
    )
    # Mark messages RECEIVED by user as deleted_by_receiver
    messages_collection.update_many(
        {'sender_id': int(target_user_id), 'receiver_id': int(user_id)},
        {'$set': {'deleted_by_receiver': True}}
    )

def delete_messages(message_ids, user_id, mode='local'):
    # message_ids are strings (ObjectIds)
    from bson.objectid import ObjectId
    try:
        obj_ids = [ObjectId(mid) for mid in message_ids]
    except:
        return # Invalid ID

    if mode == 'everyone':
        # Only for messages sent by user
        query = {'_id': {'$in': obj_ids}, 'sender_id': int(user_id)}
        messages_collection.update_many(query, {'$set': {'is_revoked': True}})
    else:
        # Local Delete
        # Sent by user
        messages_collection.update_many(
            {'_id': {'$in': obj_ids}, 'sender_id': int(user_id)},
            {'$set': {'deleted_by_sender': True}}
        )
        # Received by user
        messages_collection.update_many(
            {'_id': {'$in': obj_ids}, 'receiver_id': int(user_id)},
            {'$set': {'deleted_by_receiver': True}}
        )
