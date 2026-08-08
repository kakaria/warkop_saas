from rest_framework import permissions
from rest_framework.permissions import BasePermission

from core.thread_local import get_current_tenant
from django.core.exceptions import ValidationError

from .models import TenantMembership


class IsAuthenticatedAndHasTenant(permissions.IsAuthenticated):
    """
    1. PASTTIN USER UDAH LOGIN
    2. PASTIIN TENANT_ID ADA DI CONTEXT
    """

    def has_permission(self, request, view):
        # cek login pake logika bawaan DRF
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False

        # cek tenant id
        tenant_id = get_current_tenant()
        if tenant_id is None:
            raise ValidationError('Tenant context is required!')

        return True


"""

        INI SEBENERNYA GAK PERLU DIPAKE WKWK
"""


class IsTenantManager(BasePermission):
    """
    BUAT MASTTIN ROLE USER YANG MASUK ADALAH MANAGER
    """

    def has_permission(self, request, view):
        # ambil requestnya dan cek apakah dia udah login
        if not request.user.is_authenticated:
            return False

        # cek ke database
        is_manager = TenantMembership.objects.filter(
            user=request.user, role=TenantMembership.Role.MANAGER
        ).exists()

        return is_manager
