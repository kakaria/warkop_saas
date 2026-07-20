from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomLoginView,
    CustomTokenRefreshView,
    StaffMemberViewSet,
    StaffProvisionView,
    StaffRoleViewSet,
    StaffViewSet,
    TenantMemberViewSet,
    TenantRegisterView,
)

router = DefaultRouter()


router.register(r"members", StaffMemberViewSet, basename="members")
router.register(r"role-members", StaffRoleViewSet, basename="role-members")
router.register(r"list-staff", TenantMemberViewSet, basename="list-staff")
router.register(r"patch-staff", StaffViewSet, basename="patch-staff")


urlpatterns = [
    path("register/", TenantRegisterView.as_view(), name="tenant-register"),
    path("invite-member/", StaffProvisionView.as_view(), name="invite-members"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("", include(router.urls)),
]
