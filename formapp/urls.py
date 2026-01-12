from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import submit_form, submit_detail, staff_login, staff_list, staff_detail

router = DefaultRouter()
router.register(r'staff-documents', views.StaffDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('submit/', submit_form),
    path('submit/<int:pk>/', submit_detail),
    path('enquiries/', views.enquiry_list),
    path('enquiries/<int:pk>/', views.enquiry_detail),
    path('staff-login/', staff_login),
    path('staff/', staff_list),
    path('staff/<int:pk>/', staff_detail),
]
