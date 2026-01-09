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
        """
        exclude_id = request.query_params.get('exclude_id')
        staffs = Staff.objects.filter(active_status=True)
        if exclude_id:
            staffs = staffs.exclude(id=exclude_id)
            
        # We can reuse StaffSerializer or a simple one
        data = staffs.values('id', 'name', 'role', 'login_id', 'profile_image')
        return Response(data)
