from django.urls import path
from .views import submit_form

urlpatterns = [
    path('submit/', submit_form),
]
