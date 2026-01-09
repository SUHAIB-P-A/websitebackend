from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from formapp.models import Staff

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # Filter notifications for the current logged-in staff
        # Assuming the auth is set up to identify the staff. 
        # For now, we return all if no specific filter, or we can filter by query param if auth isn't strict yet.
        # But ideally: return Notification.objects.filter(recipient__login_id=self.request.user.username)
        # basic implementation first.
        
        recipient_id = self.request.query_params.get('recipient_id')
        if recipient_id:
             return Notification.objects.filter(recipient_id=recipient_id)
        return Notification.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data
        recipient_id = data.get('recipient')
        
        # Check for "Broadcast" - if recipient is 'all' or specific flag
        if recipient_id == 'all':
            # Broadcast to all active staff
            staffs = Staff.objects.filter(active_status=True)
            notifications = []
            for staff in staffs:
                # Create a copy of data for each staff
                notif_data = data.copy()
                notif_data['recipient'] = staff.id
                serializer = self.get_serializer(data=notif_data)
                if serializer.is_valid():
                    self.perform_create(serializer)
                    notifications.append(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(notifications, status=status.HTTP_201_CREATED)
        
        return super().create(request, *args, **kwargs)
