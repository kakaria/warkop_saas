import pytest
from django.core.exceptions import PermissionDenied

from products.dto import CreateProductDTO
from products.models import Product
from products.services import create_product_service


@pytest.mark.django_db
def test_create_product_success(owner_membership_a, tenant_context):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    data = CreateProductDTO(
        name="Latte",
        price=1000,
        stock=100,
    )
    # Act
    product = create_product_service(
        actor_membership=owner_membership_a,
        data=data,
    )

    assert product.tenant_id == owner_membership_a.tenant_id
    assert product.price == 1000
    assert Product.objects.filter(tenant_id=owner_membership_a.tenant_id)


@pytest.mark.django_db
def test_create_product_failed_when_user_is_cashier(cashier_membership, tenant_context):
    # Arrange
    tenant_context(cashier_membership.tenant_id)

    data = CreateProductDTO(
        name="Latte",
        price=1000,
        stock=100,
    )
    # Act
    with pytest.raises(PermissionDenied):
        create_product_service(
            actor_membership=cashier_membership,
            data=data
        )

    assert Product.objects.filter(tenant_id=cashier_membership.tenant_id).count() == 0


@pytest.mark.django_db
def test_create_product_must_same_like_actor_tenant(owner_membership_a, tenant_context):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    data = CreateProductDTO(
        name="Product1",
        price=1000,
        stock=10,
    )

    # Act
    product = create_product_service(actor_membership=owner_membership_a, data=data)

    assert Product.objects.filter(id=product.id).exists()
    assert product.tenant_id == owner_membership_a.tenant_id
    assert product.created_by_id == owner_membership_a.user_id
