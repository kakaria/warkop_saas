from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.managers import StrictTenantManager


class Order(models.Model):
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="orders"
    )
    # 1 struk (order), 1 kasir
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="create_orders",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal(0.0)
    )

    class Status(models.TextChoices):
        PAID = (
            "PAID",
            _("Paid"),
        )
        PENDING = (
            "PEND",
            _("Pending"),
        )
        VOID = "VOID", _("Void")

    status = models.CharField(
        max_length=4,
        choices=Status.choices,  # biar bikin dropdown
        default=Status.PENDING,
    )

    # MANAGER SATPAM (Default)
    objects = StrictTenantManager()

    # MANAGER PINTU BELAKANG (Bypass)
    global_objects = models.Manager()


class OrderDetail(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="items")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="order_details"
    )
    quantity = models.IntegerField()

    # rekam jejak (karena nama product bisa ganti, gitu juga dengan harganya)
    product_name_at_transaction = models.CharField(max_length=150)
    price_at_transaction = models.DecimalField(max_digits=10, decimal_places=2)
