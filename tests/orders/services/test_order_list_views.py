import pytest

ORDERS_URL = "/api/v1/orders/"


@pytest.mark.usefixtures("owner_membership_a")
@pytest.mark.django_db
def test_owner_can_list_orders(api_client, owner_user, tenantA, order_pending_owner_a):
    api_client.force_authenticate(user=owner_user)

    response = api_client.get(ORDERS_URL, HTTP_X_TENANT_ID=str(tenantA.id))

    assert response.status_code == 200, response.json()
    assert [o["id"] for o in response.json()] == [order_pending_owner_a.id]


@pytest.mark.django_db
def test_cashier_cannot_list_orders(api_client, cashier_user, tenantA):
    api_client.force_authenticate(user=cashier_user)

    response = api_client.get(ORDERS_URL, HTTP_X_TENANT_ID=str(tenantA.id))

    assert response.status_code == 403


@pytest.mark.django_db
def test_list_orders_requires_authentication(api_client, tenantA):
    response = api_client.get(ORDERS_URL, HTTP_X_TENANT_ID=str(tenantA.id))

    assert response.status_code == 401


@pytest.mark.django_db
def test_member_of_tenant_a_cannot_list_orders_of_tenant_b(
    api_client, owner_user, owner_membership_a, tenantB, order_pending_owner_a
):
    api_client.force_authenticate(user=owner_user)

    response = api_client.get(ORDERS_URL, HTTP_X_TENANT_ID=str(tenantB.id))

    assert response.status_code == 403

