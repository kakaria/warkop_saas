import pytest

from core.exceptions import BusinessRuleViolation
from orders.services import fetch_order_service
from orders.models import Order

@pytest.mark.django_db
def test_fetch_order_service_success(owner_membership_a, tenant_context, order_pending_owner_a):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    # Act
    order = fetch_order_service(
        actor_membership=owner_membership_a,
        order_id=order_pending_owner_a.id
    )

    # Assert
    assert order.id == order_pending_owner_a.id
    assert order.tenant_id == owner_membership_a.tenant_id


@pytest.mark.django_db
def test_fetch_order_service_failed_when_user_is_other_tenant(
    owner_membership_b, tenant_context, order_pending_owner_a
):
    # Arrange
    tenant_context(owner_membership_b.tenant_id)

    # Act
    with pytest.raises(BusinessRuleViolation):
        fetch_order_service(
            actor_membership=owner_membership_b, order_id=order_pending_owner_a.id
        )

    # Assert
    assert order_pending_owner_a.tenant_id != owner_membership_b.tenant_id


@pytest.mark.django_db
def test_fetch_order_service_failed_when_user_is_cashier(
    cashier_membership, tenant_context, order_pending_owner_a
):
    # Arrange
    tenant_context(cashier_membership.tenant_id)
    # Act
    with pytest.raises(BusinessRuleViolation):
        fetch_order_service(
            actor_membership=cashier_membership, order_id=order_pending_owner_a.id
        )

    # Assert
    assert order_pending_owner_a.created_by != cashier_membership.user
