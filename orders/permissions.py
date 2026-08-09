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
