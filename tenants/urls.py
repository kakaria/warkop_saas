from django.urls import path

from .views import (
    CustomLoginView,
    CustomTokenRefreshView,
    RemoveMemberView,
    StaffPatchAPIView,
    StaffProvisionView,
    TenantMemberListAPIView,
    TenantRegisterView,
)

urlpatterns = [
    path("register/", TenantRegisterView.as_view(), name="tenant-register"),
    path("invite-member/", StaffProvisionView.as_view(), name="invite-members"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="refresh"),
    path("", TenantMemberListAPIView.as_view(), name="list-membership"),
    path("staff-patch/<int:pk>/", StaffPatchAPIView.as_view(), name="staff-patch"),
    path("remove/<int:pk>/", RemoveMemberView.as_view(), name="remove"),
]
