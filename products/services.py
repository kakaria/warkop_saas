from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from core.exceptions import ProductAlreadyExistsError, ProductNotFoundError
from orders.dto import CreateOrderDTO
from products.dto import CreateProductDTO
from products.models import Product, ReasonChoices, StockMovement
from tenants.models import TenantMembership

# CONSTANT ROLES
ALLOWED_PRODUCT_CREATOR_ROLES = [
    TenantMembership.Role.OWNER,
    TenantMembership.Role.MANAGER,
]


def create_product_service(
    *, actor_membership: TenantMembership, data: CreateProductDTO
) -> Product:

    # cek user (siapa yang buat product)
    if actor_membership.role not in ALLOWED_PRODUCT_CREATOR_ROLES:
        raise PermissionDenied("You not have access to do that!")

    # cek apakah ada product aktif (is_archived=False) yang namanya sama
    duplicate_product = Product.objects.filter(
        tenant_id=actor_membership.tenant_id,
        name=data.name,
        is_archived=False,
    ).exists()

    if duplicate_product:
        raise ProductAlreadyExistsError("Product dengan nama tersebut sudah ada!")

    # mencegah race condition
    try:
        # bikin productnya
        product = Product.objects.create(
            tenant_id=actor_membership.tenant_id,
            name=data.name,
            price=data.price,
            stock=data.stock,
            created_by_id=actor_membership.user_id,
        )
    except IntegrityError:
        raise ProductAlreadyExistsError("Product dengan nama tersebut sudah ada!")

    return product


def adjust_stock_service(
    *, actor_membership: TenantMembership, product_id: int, validated_data: dict
) -> StockMovement:

    # ambil reason dari payload yang udah divalidasi seralizer
    reason = validated_data["reason"]
    action = validated_data.get("action")
    quantity = validated_data.get("quantity")
    notes = validated_data.get("notes", "")

    # validasi authorization
    if (
        actor_membership.role == TenantMembership.Role.CASHIER
        and reason != ReasonChoices.SALE
    ):
        raise PermissionDenied(
            "Cashier hanya bisa melakukan stock movement untuk SALE!"
        )

    with transaction.atomic():
        # tambahin service boundaries jika gak ketemu productnya
        try:

            product = Product.objects.select_for_update().get(
                id=product_id, tenant_id=actor_membership.tenant_id, is_archived=False
            )
        except Product.DoesNotExist:
            raise ProductNotFoundError("Product tersebut tidak ada.")

        # cek jika reason Adjustment
        if reason == ReasonChoices.ADJUSTMENT:
            target_stock = validated_data["target_stock"]
            # hitung perubahan stock
            difference = target_stock - product.stock
            # cek difference
            if difference == 0:
                raise ValidationError("Target stock sama dengan jumlah stock saat ini!")

            if difference < 0:
                action = StockMovement.Action.DEDUCT
                quantity = abs(difference)
                print(action)

            else:
                action = StockMovement.Action.ADD
                quantity = difference

            product.stock = target_stock

        # kalo reason bukan Adjustment
        else:
            # kalo reason selain Adjustment
            if action == StockMovement.Action.ADD:
                product.stock += quantity
            elif action == StockMovement.Action.DEDUCT:
                # cek dulu jumlah stock yang ada
                if product.stock < quantity:
                    raise ValidationError("Jumlah stock tidak mencukupi")

                product.stock -= quantity

        # save perubahan stock terbaru
        product.save(update_fields=["stock"])
        print(f"action: {action}")
        # bikin stockmovement
        new_stock_movement = StockMovement.objects.create(
            product=product,
            action=action,
            quantity=quantity,
            reason=reason,
            notes=notes,
            created_by=actor_membership.user,
        )

        return new_stock_movement
