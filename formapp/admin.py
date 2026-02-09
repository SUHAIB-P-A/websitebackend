from django.contrib import admin
from .models import CollectionForm, Enquiry, Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "login_id", "active_status", "created_at")
    search_fields = ("name", "email", "login_id")


@admin.register(CollectionForm)
class CollectionFormAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "phone_number",
        "plus_two_percentage",
        "city",
        "created_at",
    )

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "phone",
        "message",
        "created_at",
    )