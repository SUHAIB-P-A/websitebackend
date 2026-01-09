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
