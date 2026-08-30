from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminViewMember,
    CustomLoginView,
    CustomTokenRefreshView,
    RemoveMemberView,
    StaffPatchAPIView,
    StaffProvisionView,
    StaffRoleViewSet,
    TenantMemberViewSet,
    TenantRegisterView,
)

router = DefaultRouter()


router.register(r"admin-view", AdminViewMember, basename="admin-view")
router.register(r"role-members", StaffRoleViewSet, basename="role-members")
router.register(r"list-staff", TenantMemberViewSet, basename="list-staff")

urlpatterns = [
    path("register/", TenantRegisterView.as_view(), name="tenant-register"),
    path("invite-member/", StaffProvisionView.as_view(), name="invite-members"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("staff-patch/<int:pk>/", StaffPatchAPIView.as_view(), name="staff-patch"),
    path("remove/<int:pk>/", RemoveMemberView.as_view(), name="remove"),
    path("", include(router.urls)),
]
