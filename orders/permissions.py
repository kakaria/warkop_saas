from rest_framework.permissions import BasePermission

from tenants.models import TenantMembership


class IsTenantCashier(BasePermission):
    """
    buat mastiini user adalah cashier sesuai tenant_id

    """

    def has_permission(self, request, view):
        # ambil requestnya cek apakah udah login
        if not request.user.is_authenticated:
            return False

        # cek ke database
        is_cashier = TenantMembership.objects.filter(
            user=request.user, role=TenantMembership.Role.CASHIER
        ).exists()

        return is_cashier


class IsTenantManagerOrOwner(BasePermission):
    """
    buat mastiini user adalah manager or owner sesuai tenant_id

    """

    def has_permission(self, request, view):
        # ambil requestnya cek apakah udah login
        if not request.user.is_authenticated:
            print("hehe")
            return False

        # cek ke database
        is_owner_or_manager = TenantMembership.objects.filter(
            user=request.user,
            role__in=[TenantMembership.Role.OWNER, TenantMembership.Role.MANAGER],
        ).exists()

        return is_owner_or_manager
