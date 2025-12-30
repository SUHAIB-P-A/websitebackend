from django.urls import path
from . import views
from .views import submit_form, submit_detail, staff_login, staff_list, staff_detail

urlpatterns = [
    path('submit/', submit_form),
    path('submit/<int:pk>/', submit_detail),
    path('enquiries/', views.enquiry_list),
    path('enquiries/<int:pk>/', views.enquiry_detail),
    path('staff-login/', staff_login),
    path('staff/', staff_list),
    path('staff/<int:pk>/', staff_detail),
]
