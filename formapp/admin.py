from django.contrib import admin
from .models import CollectionForm


@admin.register(CollectionForm)
class CollectionFormAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone_number",
        "plus_two_percentage",
        "city",
        "created_at",
    )
