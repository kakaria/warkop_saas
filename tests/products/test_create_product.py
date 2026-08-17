import pytest

from products.models import Product
from products.services import create_product_service


@pytest.mark.django_db
def test_create_product_success(owner_membership_a, tenant_context):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    validated_data = {"name": "product test", "price": 1000, "stock": 10}

    # Act
    product = create_product_service(
        actor_membership=owner_membership_a,
        validated_data=validated_data,
    )

    assert product.tenant_id == owner_membership_a.tenant_id
    assert product.price == 1000
    assert Product.objects.filter(tenant_id=owner_membership_a.tenant_id)


@pytest.mark.django_db
def test_create_product_success(owner_membership_a, tenant_context):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    validated_data = {"name": "product test", "price": 1000, "stock": 10}

    # Act
    product = create_product_service(
        actor_membership=owner_membership_a,
        validated_data=validated_data,
    )

    assert product.tenant_id == owner_membership_a.tenant_id
    assert product.price == 1000
    assert Product.objects.filter(tenant_id=owner_membership_a.tenant_id)
