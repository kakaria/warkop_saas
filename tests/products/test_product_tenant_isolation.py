import pytest
from django.urls import reverse

from products.models import Product


@pytest.mark.django_db
def test_tenant_can_access_own_product(
    owner_membership_a,
    product,
    tenant_context,
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    # Act
    new_product = Product.objects.get(id=product.id)

    # Assert
    assert new_product.id == product.id
    assert new_product.tenant_id == owner_membership_a.tenant_id


@pytest.mark.django_db
def test_tenant_cannot_see_other_tenant_product(
    owner_membership_a, productB, tenant_context
):
    # Arrange
    tenant_context(owner_membership_a)

    # Act
    product = Product.objects.filter(id=productB.id)

    # Assert
    assert product.count() == 0


@pytest.mark.django_db
def test_user_cannot_see_product_in_other_tenant(api_client, owner_user, tenantB):
    api_client.force_authenticate(user=owner_user)

    url = reverse("products-list")
    response = api_client.get(url, HTTP_X_TENANT_ID=str(tenantB.id))

    print(response.status_code)
    print(response.data)
    print(response.request)

    assert response.status_code == 403, response.data
    assert response.status_code == 403
