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

        # Logic: Messages where (Sender is U1 AND not deleted by sender) OR (Receiver is U1 AND not deleted by receiver)
        # We assume U1 is the viewer.
        
        msgs = Message.objects.filter(
            (Q(sender_id=u1) & Q(receiver_id=u2) & Q(deleted_by_sender=False)) |
            (Q(sender_id=u2) & Q(receiver_id=u1) & Q(deleted_by_receiver=False))
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
            # Must exclude if deleted by current user
            from django.db.models import Subquery, OuterRef, Count, Max, Value, DateTimeField, IntegerField
            from django.db.models.functions import Coalesce

            last_msg_qs = Message.objects.filter(
                (Q(sender_id=OuterRef('pk')) & Q(receiver_id=current_user_id) & Q(deleted_by_receiver=False)) |
                (Q(sender_id=current_user_id) & Q(receiver_id=OuterRef('pk')) & Q(deleted_by_sender=False))
            ).order_by('-timestamp').values('timestamp')[:1]

            # Subquery for unread count (messages sent BY the staff TO current user)
            # Must exclude if deleted by current user (receiver)
            unread_qs = Message.objects.filter(
                sender_id=OuterRef('pk'),
                receiver_id=current_user_id,
                is_read=False,
                deleted_by_receiver=False
            ).values('sender').annotate(count=Count('id')).values('count')

            from django.db.models import F
            staffs = staffs.annotate(
                last_message_time=Subquery(last_msg_qs, output_field=DateTimeField()),
                unread_count=Coalesce(Subquery(unread_qs, output_field=IntegerField()), Value(0))
            ).order_by(F('last_message_time').desc(nulls_last=True), 'name')
            
            # Check if this is a polling request (lightweight)
            is_polling = request.query_params.get('polling') == 'true'
            
            fields_to_fetch = ['id', 'name', 'role', 'login_id', 'unread_count', 'last_message_time']
            if not is_polling:
                fields_to_fetch.append('profile_image')

            data = staffs.values(*fields_to_fetch)
            return Response(data)

        # Fallback if no exclude_id provided
        # Check if this is a polling request (lightweight)
        is_polling = request.query_params.get('polling') == 'true'
        
        fields_to_fetch = ['id', 'name', 'role', 'login_id']
        if not is_polling:
            fields_to_fetch.append('profile_image')

        # Fallback if no exclude_id provided
        data = staffs.values(*fields_to_fetch)
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
        
        count = Message.objects.filter(receiver_id=user_id, is_read=False, deleted_by_receiver=False).count()
        return Response({'count': count})

    @action(detail=False, methods=['post'])
    def delete_conversation(self, request):
        """
        Delete messages between user_id and target_user_id.
        usage: POST /api/chat/delete_conversation/
        body: { "user_id": X, "target_user_id": Y }
        """
        user_id = request.data.get('user_id')
        target_user_id = request.data.get('target_user_id')
        # mode param is ignored; strictly enforced local delete.

        if not user_id or not target_user_id:
            return Response({'error': 'Missing user_id or target_user_id'}, status=status.HTTP_400_BAD_REQUEST)

        # Soft delete (Local) - Only clear for the requesting user
        # Update messages sent by user
        Message.objects.filter(
            sender_id=user_id,
            receiver_id=target_user_id
        ).update(deleted_by_sender=True)
        
        # Update messages received by user
        Message.objects.filter(
            sender_id=target_user_id,
            receiver_id=user_id
        ).update(deleted_by_receiver=True)

        return Response({'status': 'deleted', 'mode': 'local'})

    @action(detail=False, methods=['post'])
    def delete_messages(self, request):
        """
        Delete specific messages by ID.
        usage: POST /api/chat/delete_messages/
        body: { "message_ids": [1, 2, 3], "user_id": X }
        """
        message_ids = request.data.get('message_ids', [])
        user_id = request.data.get('user_id')
        mode = request.data.get('mode', 'local')
        
        if not message_ids:
             return Response({'error': 'Missing message_ids'}, status=status.HTTP_400_BAD_REQUEST)

        msgs = Message.objects.filter(id__in=message_ids)
        
        if user_id:
            if mode == 'everyone':
                # Delete for everyone: Only applicable to messages SENT by this user.
                # Mark as revoked (content replaced), but keep visible in query so text can be shown.
                msgs.filter(sender_id=user_id).update(is_revoked=True)
                
                # IMPORTANT: Do NOT set deleted_by_sender/receiver for 'everyone' mode, 
                # because we want to show "You deleted this message" / "This message was deleted"
            else:
                # Local delete
                msgs.filter(sender_id=user_id).update(deleted_by_sender=True)
                msgs.filter(receiver_id=user_id).update(deleted_by_receiver=True)
        else:
             # Fallback to request.user if available (though likely anonymous or staff via session)
             if request.user.is_authenticated:
                if mode == 'everyone':
                    msgs.filter(sender=request.user).update(is_revoked=True)
                else:
                    msgs.filter(sender=request.user).update(deleted_by_sender=True)
                    msgs.filter(receiver=request.user).update(deleted_by_receiver=True)
            
        return Response({'status': 'success'})
