from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CollectionForm, Enquiry, Notification, Staff


@receiver(post_save, sender=Enquiry)
def notify_new_enquiry(sender, instance, created, **kwargs):
    """
    On creation: notify admins and the assigned staff member about the new enquiry.
    Assignment notifications are only sent on creation to avoid duplicate alerts on
    subsequent updates.
    """
    if not created:
        return

    # Notify all admin users
    admins = Staff.objects.filter(login_id='admin')
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            title="New Enquiry Received",
            message=f"New enquiry from {instance.name}",
            link="/portal/enquiries",
            type="System",
        )

    # Notify the assigned staff member (set by auto-allocation at creation time)
    if instance.assigned_staff:
        Notification.objects.create(
            recipient=instance.assigned_staff,
            title="New Enquiry Assigned",
            message=f"You have been assigned enquiry: {instance.name}",
            link="/portal/enquiries",
            type="Assignment",
        )


@receiver(post_save, sender=CollectionForm)
def notify_new_student(sender, instance, created, **kwargs):
    """
    On creation: notify the assigned staff member about the new student form.
    """
    if not created or not instance.assigned_staff:
        return

    Notification.objects.create(
        recipient=instance.assigned_staff,
        title="New Student Assigned",
        message=f"You have been assigned student: {instance.full_name}",
        link="/portal/students",
        type="Assignment",
    )
