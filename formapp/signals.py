from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Enquiry, CollectionForm, Notification, Staff

@receiver(post_save, sender=Enquiry)
def notify_new_enquiry(sender, instance, created, **kwargs):
    """
    1. Notify Admins when a new Enquiry is created.
    2. Notify Staff if assigned during creation or update.
    """
    if created:
        # Notify Admins
        admins = Staff.objects.filter(login_id='admin') # Or role check if available
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                title="New Enquiry Received",
                message=f"New enquiry from {instance.name}",
                link=f"/portal/enquiries", # Admin can find it in list
                type="System"
            )

    # Check for assignment (Using post_save is tricky for 'change' without keeping track of old value, 
    # but we can check if assigned_staff is set).
    # For robust "Assignment Change" detection, we usually need pre_save or __init__ tracking.
    # For now, if assigned_staff is present, we notify (might result in duplicates on edits, but acceptable for mvp).
    # Better approach: Check if it's a fresh assignment.
    if instance.assigned_staff:
        # We can optimize this by checking if it changed, but let's keep it simple: 
        # "You have an enquiry assigned" notification on every save with assignment might be annoying.
        # Let's trust that the 'created' block covers initial assignment if auto-allocated.
        if created:
             Notification.objects.create(
                recipient=instance.assigned_staff,
                title="New Enquiry Assigned",
                message=f"You have been assigned enquiry: {instance.name}",
                link="/portal/enquiries", 
                type="Assignment"
            )


@receiver(post_save, sender=CollectionForm)
def notify_new_student(sender, instance, created, **kwargs):
    """
    Notify Staff when a Student is assigned to them.
    """
    if instance.assigned_staff:
        if created:
             Notification.objects.create(
                recipient=instance.assigned_staff,
                title="New Student Assigned",
                message=f"You have been assigned student: {instance.first_name} {instance.last_name}",
                link="/portal/students", 
                type="Assignment"
            )
        # TODO: handle re-assignment updates if needed
