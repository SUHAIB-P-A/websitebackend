from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import submit_form, submit_detail, staff_login, staff_list, staff_detail

router = DefaultRouter()
router.register(r'staff-documents', views.StaffDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Specific paths BEFORE generic <pk> paths to avoid pattern conflicts
    path('submit/', submit_form),
    path('submit/<int:pk>/', submit_detail),
    path('enquiries/', views.enquiry_list),
    path('enquiries/<int:pk>/', views.enquiry_detail),
    path('staff-login/', staff_login),
    # Specific staff endpoints
    path('staff/reallocate/', views.reallocate_leads),
    path('dashboard/', views.dashboard_stats),
    # Generic staff endpoints (AFTER specific routes)
    path('staff/', staff_list),
    path('staff/<int:pk>/', staff_detail),

    # Organization endpoints
    path('org-login/', views.org_login),
    path('org-students/', views.org_students),
    path('org-enquiries/', views.org_enquiries),
    path('organizations/', views.org_list),
    path('organizations/<int:pk>/', views.org_detail),
]
