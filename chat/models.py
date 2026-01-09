from django.db import models
from formapp.models import Staff

class Message(models.Model):
    # We use Staff model for both sender and receiver.
    # If the system ever expands to include non-staff users (like Students), this might need to be generic or nullable.
    # But for "Admin <-> Staff" and "Staff <-> Staff", this is perfect.
    
    sender = models.ForeignKey(Staff, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(Staff, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender} to {self.receiver} at {self.timestamp}"
