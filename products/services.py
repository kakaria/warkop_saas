from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from products.models import Product
from tenants.models import TenantMembership

# CONSTANT ROLES
ALLOWED_PRODUCT_CREATOR_ROLES = [
    TenantMembership.Role.OWNER,
    TenantMembership.Role.MANAGER,
]


def create_product_service(
    actor_membership: TenantMembership, validated_data: dict
) -> Product:

    # cek user (siapa yang buat product)
    if actor_membership.role not in ALLOWED_PRODUCT_CREATOR_ROLES:
        raise PermissionDenied("You not have access to do that!")

    # cek apakah ada product aktif (is_archived=False) yang namanya sama
    duplicate_product = Product.objects.filter(
        tenant_id=actor_membership.tenant_id,
        name=validated_data["name"],
        is_archived=False,
    ).exists()

    if duplicate_product:
        raise ValidationError("Product dengan nama tersebut sudah ada!")

    # mencegah race condition
    try:
        # bikin productnya
        product = Product.objects.create(
            tenant=actor_membership.tenant, **validated_data
        )
    except IntegrityError:
        raise ValidationError("Product dengan nama tersebut sudah ada!")

    return product
