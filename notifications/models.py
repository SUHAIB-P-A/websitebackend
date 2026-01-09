from django.db import models
from django.conf import settings
# If using a custom user model (Staff), we should probably refer to it directly or via settings.AUTH_USER_MODEL if it was swapped.
# The previous migration used settings.AUTH_USER_MODEL.
# However, the user also has a 'Staff' model in 'formapp'.
# Let's check settings.py for AUTH_USER_MODEL. It usually defaults to 'auth.User'.
# If the previous migration pointed to AUTH_USER_MODEL, and that is default User, but the system uses 'Staff' separately...
# Wait, let's re-read migration 0001_initial.py.
# dependencies = [ migrations.swappable_dependency(settings.AUTH_USER_MODEL), ]
# This links to the Django User model.
# But the request talks about "Staffs".
# The 'formapp.Staff' model might be independent of 'auth.User' or linked.
# Let's check 'formapp/models.py' again. It has login_id, password... it looks like a custom auth model but maybe not hooked into AUTH_USER_MODEL setting.
# Steps 31 showed formapp.models.Staff. It inherits models.Model. It has check_password.
# It does NOT look like it replaces the default User model in settings.py (I didn't see AUTH_USER_MODEL = 'formapp.Staff' in Step 21).
# So, the Notifications should probably point to 'formapp.Staff' if we want to notify "Staffs".
# BUT the migration 0001_initial.py pointed to settings.AUTH_USER_MODEL.
# Only two possibilities:
# 1. The previous dev intended to use Django Users but the actual business logic uses formapp.Staff.
# 2. settings.AUTH_USER_MODEL IS set to something I missed? No, Step 21 didn't show it.
# If I follow the existing migration strictly, it points to User. If I want it to work for "Staff" (formapp.Staff), I should change it.
# Changing it now would mismatch the migration 0001.
# IF I change the model definition to use 'formapp.Staff', I will need a new migration.
# Since the 'notifications' app seems unused (missing models.py), maybe I can delete the old migration or make a new one.
# For now, I will define the model to use `formapp.Staff` because the requirement is "Admin sends to Staffs".
# Using the default User model might be wrong if "Staffs" are in `formapp.Staff`.
# Let's import Staff from formapp.models.

from formapp.models import Staff

class Notification(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    
    CATEGORY_CHOICES = [
        ('Alert', 'Alert'),
        ('Event', 'Event'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Event')
    
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Normal', 'Normal'),
        ('Low', 'Low'),
    ]
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Changed from settings.AUTH_USER_MODEL to Staff because that is the domain entity.
    # Note: I will need to handle migration conflicts.
    recipient = models.ForeignKey(Staff, related_name='notifications', on_delete=models.CASCADE, null=True, blank=True)
    
    # Sender can be Admin (who might not be a Staff object, or is a User object).
    # If Admin is just a Staff with role='admin', then this works. 
    # If Admin is a Django Superuser, this might fail if sender is strictly Staff.
    # Let's make sender nullable or generic. For now, let's assume sender is also a Staff (Admin role) or null (System).
    sender = models.ForeignKey(Staff, related_name='sent_notifications', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.title} - {self.recipient}"
