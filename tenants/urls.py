
from django.urls import path

from .views import StaffProvisionView, TenantRegisterView


urlpatterns = [
    path('register/', TenantRegisterView.as_view(), name='tenant_reqister'),
    path('invite-member/', StaffProvisionView.as_view(), name='invite-members'),
]
