from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from core.thread_local import get_current_tenant

from .models import TenantMembership


class IsAuthenticatedAndHasTenant(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        # cek login pake logika bawaan DRF
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False

        # cek tenant id
        tenant_id = get_current_tenant()
        if tenant_id is None:
            raise PermissionDenied("Tenant context is required!")

        has_membership = TenantMembership.objects_global.filter(
            user=request.user, tenant_id=tenant_id, left_at=None
        ).exists()

        if not has_membership:
            raise PermissionDenied("Anda tidak memiliki akses ke tenant ini")

        return True


class IsTenantManagerOrOwner(BasePermission):
    """
    buat mastiini user adalah manager or owner sesuai tenant_id

    """

    def has_permission(self, request, view):

        # ambil requestnya cek apakah udah login
        if not request.user or not request.user.is_authenticated:
            return False

        tenant_id = get_current_tenant()

        # cek ke database
        is_owner_or_manager = TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.MANAGER],
            left_at__isnull=True,
        ).exists()

        return is_owner_or_manager


class IsTenantOwner(BasePermission):
    """
    buat mastiini user adalah manager or owner sesuai tenant_id

    """

    def has_permission(self, request, view):

        # ambil requestnya cek apakah udah login
        if not request.user or not request.user.is_authenticated:
            return False

        tenant_id = get_current_tenant()

        # cek ke database
        is_owner = TenantMembership.objects.filter(
            user=request.user,
            tenant_id=tenant_id,
            role=TenantMembership.Role.OWNER,
            left_at__isnull=True,
        ).exists()

        return is_owner


class IsTenantManager(BasePermission):
    """
    BUAT MASTTIN ROLE USER YANG MASUK ADALAH MANAGER
    """

    def has_permission(self, request, view):
        # ambil requestnya dan cek apakah dia udah login
        if not request.user.is_authenticated:
            return False

        tene
        # cek ke database
        is_manager = TenantMembership.objects.filter(
            user=request.user, role=TenantMembership.Role.MANAGER
        ).exists()

        return is_manager
