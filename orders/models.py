from django.conf import settings
from django.db import models
from django.db.models import constraints
from django.utils.translation import gettext_lazy as _

from core.managers import StrictTenantManager


class Order(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="orders"
    )
    # 1 struk (order), 1 kasir
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="create_orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.IntegerField()

    # MANAGER SATPAM (Default)
    objects = StrictTenantManager()

    # MANAGER PINTU BELAKANG (Bypass)
    global_objects = models.Manager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0), name="total_price_gte_0"
            )
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_items"
    )
    quantity = models.IntegerField()

    # rekam jejak (karena nama product bisa ganti, gitu juga dengan harganya)
    product_name_at_transaction = models.CharField(max_length=150)
    price_at_transaction = models.IntegerField()
    sub_total = models.IntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="quantity_must_than_0"
            ),
        ]
