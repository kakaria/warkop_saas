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
                condition=models.Q(price__gte=0), name="product_price_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(stock__gte=0), name="product_stock_gte_0"
            ),
            # unique tenant dan name product
            models.UniqueConstraint(
                fields=["tenant", "name"],
                condition=Q(is_archived=False),
                name="unique_tenant_name_product",
            ),
        ]


class ReasonChoices(models.TextChoices):
    RESTOCK = "RESTOCK", "Restock"
    DAMAGED = "DAMAGED", "Damaged"
    EXPIRED = "EXPIRED", "Expired"
    SALE = "SALE", "Sale"
    LOST = "LOST", "Lost"
    ADJUSTMENT = "ADJUSTMENT", "Adjustment"
    OTHER = "OTHER", "Other"


class StockMovement(models.Model):

    class Action(models.TextChoices):
        ADD = "ADD", "Add"
        DEDUCT = "DEDUCT", "Deduct"

    # bikin fieldnya
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="stock_movement"
    )
    action = models.CharField(
        max_length=10,
        choices=Action.choices,
    )

    quantity = (
        models.PositiveIntegerField()
    )  # biar gak perlu nulis - (karena udah ada action)

    reason = models.CharField(max_length=10, choices=ReasonChoices.choices)

    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )

    created_by = models.ForeignKey(
        "users.User", on_delete=models.PROTECT, related_name="stock_movements_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="stock_movement_quantity_must_be_positive",
            ),
            models.CheckConstraint(
                condition=~Q(reason=ReasonChoices.OTHER) | ~Q(notes=""),
                name="notes_required_if_reason_other",
            ),
        ]
