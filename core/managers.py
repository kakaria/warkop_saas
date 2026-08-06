from django.db import models
from django.db.models import Q

from .thread_local import get_current_tenant


class StrictTenantManager(models.Manager):
    def get_queryset(self):
        tenant_id = get_current_tenant()
        queryset = super().get_queryset()

        if tenant_id is None:
            return queryset.none()

        return queryset.filter(tenant_id=tenant_id)


class ActiveMembershipManager(StrictTenantManager):
    """
    custom manager khusus TenantMembership, filter tenant_id dan member yang masih aktif (left_at = Null)
    """

    def get_queryset(self):
        # ambil queryset si StrictTenantManager (yang udah filter tenant_id) dan tambahin filter (membership yang aktif)
        return super().get_queryset().filter(left_at__isnull=True)


class ProductTenantManager(models.Manager):

    def get_queryset(self):
        tenant_id = get_current_tenant()
        queryset = super().get_queryset()

        if tenant_id is None:
            return queryset.none()

        return queryset.filter(tenant_id=tenant_id, is_archived=False)
