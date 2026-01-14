from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .mongo_client import save_message, get_conversation, get_last_message, get_unread_count, mark_as_read, delete_conversation_local, delete_messages as delete_messages_mongo
from formapp.models import Staff
from formapp.serializers import StaffSerializer
import datetime 

class MessageViewSet(viewsets.ViewSet):
    """
    A simplified ViewSet for Chat Messages backed by MongoDB.
    No longer inherits ModelViewSet because we aren't using Django ORM for messages.
    """

    def create(self, request):
        """
        Send a message.
        POST /api/chat/
        Body: { sender: X, receiver: Y, content: "..." } OR { sender_id: X, receiver_id: Y, content: "..." }
        """
        data = request.data
        
        # Normalize field names - accept both 'sender' and 'sender_id'
        normalized_data = {
            'sender_id': data.get('sender_id') or data.get('sender'),
            'receiver_id': data.get('receiver_id') or data.get('receiver'),
            'content': data.get('content')
        }
        
        if not all(normalized_data.values()):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify users exist in SQL
        if not Staff.objects.filter(id=normalized_data['sender_id']).exists():
             return Response({'error': 'Invalid sender_id'}, status=status.HTTP_400_BAD_REQUEST)
        if not Staff.objects.filter(id=normalized_data['receiver_id']).exists():
             return Response({'error': 'Invalid receiver_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            msg = save_message(normalized_data)
            return Response(msg, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """
        Get messages between user_id_1 and user_id_2
        usage: /api/chat/conversation/?user1=X&user2=Y
        """
        u1 = request.query_params.get('user1')
        u2 = request.query_params.get('user2')
        
        if not u1 or not u2:
            return Response({'error': 'Missing user1 or user2 params'}, status=status.HTTP_400_BAD_REQUEST)

        msgs = get_conversation(u1, u2)
        
        # Mark messages from u2 as read by u1 (assuming u1 is the requester)
        # In a real app we'd verify request.user
        mark_as_read(sender_id=u2, receiver_id=u1)
        
        return Response(msgs)

    @action(detail=False, methods=['get'])
    def users(self, request):
        """
        Get list of users to chat with, annotated with stats from Mongo.
        usage: /api/chat/users/?exclude_id=X
        """
        current_user_id = request.query_params.get('exclude_id')
        staffs = Staff.objects.filter(active_status=True)
        
        if current_user_id:
            try:
                current_user_id = int(current_user_id)
                staffs = staffs.exclude(id=current_user_id)
            except ValueError:
                pass # safely ignore invalid id
            
        # Optimization: Fetch basic fields
        is_polling = request.query_params.get('polling') == 'true'
        fields_to_fetch = ['id', 'name', 'role', 'login_id']
        if not is_polling:
            fields_to_fetch.append('profile_image')
            
        staff_data = list(staffs.values(*fields_to_fetch))
        
        if current_user_id:
            # Annotate with data from Mongo
            for s in staff_data:
                other_id = s['id']
                # Unread count (Messages SENT by other_id TO current_user_id)
                s['unread_count'] = get_unread_count(sender_id=other_id, receiver_id=current_user_id)
                
                # Last message time
                s['last_message_time'] = get_last_message(current_user_id, other_id)
            
            
            # Sort by last_message_time desc
            # Handle both timezone-aware and naive datetimes
            def sort_key(user):
                ts = user.get('last_message_time')
                if ts is None:
                    # Return a very old date for users with no messages
                    return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                # If timestamp is already a datetime object, ensure it's timezone-aware
                if isinstance(ts, datetime.datetime):
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=datetime.timezone.utc)
                    return ts
                # If it's a string (from ISO format), parse it
                if isinstance(ts, str):
                    try:
                        return datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    except:
                        return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
                return datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            
            staff_data.sort(key=sort_key, reverse=True)
            
        return Response(staff_data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get total unread count for a user (across all conversations? Or specific?)
        The old API seemed to imply total unread messages for detailed view.
        usage: /api/chat/unread_count/?user_id=X
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
             return Response({'error': 'Missing user_id param'}, status=status.HTTP_400_BAD_REQUEST)
        
        # We can sum up all unread messages for this receiver
        # Implementation in mongo_client needed if we want TOTAL unread.
        # For now, let's reuse the per-sender logic if the frontend iterates, 
        # OR just return a sum if we modify mongo_client.
        # Let's assume the frontend asks for specific or we add a 'total_unread' helper.
        
        # Quick fix: Count any unread message where receiver_id == user_id
        from .mongo_client import messages_collection
        total = messages_collection.count_documents({
            'receiver_id': int(user_id), 
            'is_read': False, 
            'deleted_by_receiver': False
        })
        return Response({'count': total})

    @action(detail=False, methods=['post'])
    def delete_conversation(self, request):
        user_id = request.data.get('user_id')
        target_user_id = request.data.get('target_user_id')

        if not user_id or not target_user_id:
            return Response({'error': 'Missing user_id or target_user_id'}, status=status.HTTP_400_BAD_REQUEST)

        delete_conversation_local(user_id, target_user_id)
        return Response({'status': 'deleted', 'mode': 'local'})

    @action(detail=False, methods=['post'])
    def delete_messages(self, request):
        message_ids = request.data.get('message_ids', [])
        user_id = request.data.get('user_id')
        mode = request.data.get('mode', 'local')
        
        if not message_ids:
             return Response({'error': 'Missing message_ids'}, status=status.HTTP_400_BAD_REQUEST)

        delete_messages_mongo(message_ids, user_id, mode)
        return Response({'status': 'success'})

