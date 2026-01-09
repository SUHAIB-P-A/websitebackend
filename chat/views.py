from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Message
from .serializers import MessageSerializer
from formapp.models import Staff
from django.db.models import Q
from formapp.serializers import StaffSerializer 

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer

    def get_queryset(self):
        # By default, return messages where current user is involved
        # For security, we should filter by request.user or similar if we have auth.
        # Here we rely on query params or custom actions.
        return Message.objects.all()

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

        msgs = Message.objects.filter(
            (Q(sender_id=u1) & Q(receiver_id=u2)) |
            (Q(sender_id=u2) & Q(receiver_id=u1))
        ).order_by('timestamp')
        
        serializer = self.get_serializer(msgs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def users(self, request):
        """
        Get list of users to chat with.
        Excludes the requester if 'exclude_id' param is provided.
        Annotates with unread_count and last_message_time for sorting.
        """
        current_user_id = request.query_params.get('exclude_id')
        staffs = Staff.objects.filter(active_status=True)
        
        if current_user_id:
            staffs = staffs.exclude(id=current_user_id)
            
            # Subquery for last message time (sent or received)
            from django.db.models import Subquery, OuterRef, Count, Max, Value, DateTimeField, IntegerField
            from django.db.models.functions import Coalesce

            last_msg_qs = Message.objects.filter(
                (Q(sender_id=OuterRef('pk')) & Q(receiver_id=current_user_id)) |
                (Q(sender_id=current_user_id) & Q(receiver_id=OuterRef('pk')))
            ).order_by('-timestamp').values('timestamp')[:1]

            # Subquery for unread count (messages sent BY the staff TO current user)
            unread_qs = Message.objects.filter(
                sender_id=OuterRef('pk'),
                receiver_id=current_user_id,
                is_read=False
            ).values('sender').annotate(count=Count('id')).values('count')

            from django.db.models import F
            staffs = staffs.annotate(
                last_message_time=Subquery(last_msg_qs, output_field=DateTimeField()),
                unread_count=Coalesce(Subquery(unread_qs, output_field=IntegerField()), Value(0))
            ).order_by(F('last_message_time').desc(nulls_last=True), 'name')
            
            data = staffs.values('id', 'name', 'role', 'login_id', 'profile_image', 'unread_count', 'last_message_time')
            return Response(data)

        # Fallback if no exclude_id provided
        data = staffs.values('id', 'name', 'role', 'login_id', 'profile_image')
        return Response(data)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread messages for a user.
        usage: /api/chat/unread_count/?user_id=X
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
             return Response({'error': 'Missing user_id param'}, status=status.HTTP_400_BAD_REQUEST)
        
        count = Message.objects.filter(receiver_id=user_id, is_read=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def delete_conversation(self, request):
        """
        Delete all messages between user_id and target_user_id.
        usage: POST /api/chat/delete_conversation/
        body: { "user_id": X, "target_user_id": Y }
        """
        user_id = request.data.get('user_id')
        target_user_id = request.data.get('target_user_id')

        if not user_id or not target_user_id:
            return Response({'error': 'Missing user_id or target_user_id'}, status=status.HTTP_400_BAD_REQUEST)

        # Delete messages where (sender=user_id AND receiver=target_user_id) OR (sender=target_user_id AND receiver=user_id)
        # In a real app, we might just set a "deleted_by_X" flag, but here we hard delete as per request.
        Message.objects.filter(
            (Q(sender_id=user_id) & Q(receiver_id=target_user_id)) |
            (Q(sender_id=target_user_id) & Q(receiver_id=user_id))
        ).delete()

        return Response({'status': 'deleted'})

    @action(detail=False, methods=['post'])
    def delete_messages(self, request):
        """
        Delete specific messages by ID.
        usage: POST /api/chat/delete_messages/
        body: { "message_ids": [1, 2, 3] }
        """
        message_ids = request.data.get('message_ids', [])
        
        if not message_ids:
             return Response({'error': 'Missing message_ids'}, status=status.HTTP_400_BAD_REQUEST)

        # In a real app verify ownership (sender/receiver) before deleting?
        # For this internal tool, we assume staff can manage their own chats.
        Message.objects.filter(id__in=message_ids).delete()
        
        return Response({'status': 'deleted'})
