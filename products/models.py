from django.db import models
from django.db.models import Q

from core.managers import ProductTenantManager


class Product(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    stock = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)

    # PANGGIL SI SATPAM (Default dengan logika OR)
    objects = ProductTenantManager()

    # PANGGIL MANAGER PINTU BELAKANG (Bypass)
    global_objects = models.Manager()

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "is_archived"]),
        ]
        constraints = [
            # biar price > 0
            models.CheckConstraint(
                check=models.Q(price__gte=0), name="product_price_gte_0"
            ),
            models.CheckConstraint(
                check=models.Q(stock__gte=0), name="product_stock_gte_0"
            ),
            # unique tenant dan name product
            models.UniqueConstraint(
                fields=["tenant", "name"],
                condition=Q(is_archived=False),
                name="unique_tenant_name_product",
            ),
        ]
