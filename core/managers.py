from django.db import models
from django.db.models import Q
from .thread_local import get_current_tenant

class StrictTenantManager(models.Manager):
    """
        digunakan untuk table transaksi (Order, OrderItem). harus ada Tenant
    """
    def get_queryset(self):
        tenant_id = get_current_tenant()
        queryset = super().get_queryset()

        if tenant_id is None:
            return queryset.none()

        return queryset.filter(tenant_id = tenant_id)

class ProductTenantManager(models.Manager):

    def get_queryset(self):
        tenant_id = get_current_tenant()
        queryset = super().get_queryset()

        if tenant_id is None:
            # opsional: kalo gak ada tenant, kasih yang product global aja
            return queryset.filter(tenant__isnull=True)
        #  pake OR: ambil product local (yang sesuai tenant_id) ATAU product global (tenant_nya null)
        return queryset.filter(Q(tenant_id=tenant_id) | Q(tenant__isnull=True))
