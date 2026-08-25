import threading

import pytest
from django.db import close_old_connections, transaction

from core.exceptions import BusinessRuleViolation, ResourceNotFound
from orders.models import Order
from orders.services import order_paid_service


@pytest.mark.django_db
def test_order_paid_service_success(
    owner_membership_a, tenant_context, order_pending_owner_a
):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order = order_pending_owner_a
    initial_order_status = order.status

    print(f"debug: {initial_order_status}")

    order_paid = order_paid_service(
        actor_membership=owner_membership_a,
        order_id=order.id,
    )

    order_paid.refresh_from_db()

    assert order_paid.status == Order.Status.PAID
    assert order_paid.tenant_id == owner_membership_a.tenant_id


@pytest.mark.django_db
def test_order_paid_service_failed_when_order_status_is_paid(
    owner_membership_a, tenant_context, order_paid_owner_a
):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order = order_paid_owner_a

    with pytest.raises(BusinessRuleViolation) as exc:
        order_paid_service(
            actor_membership=owner_membership_a,
            order_id=order.id,
        )

    order.refresh_from_db()

    assert order.status == Order.Status.PAID
    assert "hanya order dengan status pending" in str(exc.value).lower()


@pytest.mark.django_db
def test_order_paid_service_failed_when_order_status_is_void(
    owner_membership_a, tenant_context, order_paid_owner_a
):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order = order_paid_owner_a

    with pytest.raises(BusinessRuleViolation) as exc:
        order_paid_service(
            actor_membership=owner_membership_a,
            order_id=order.id,
        )

    order.refresh_from_db()

    assert order.status == Order.Status.VOID
    assert "hanya order dengan status pending" in str(exc.value).lower()


@pytest.mark.django_db
def test_order_paid_service_failed_when_order_was_in_other_tenant(
    owner_membership_a, tenant_context, order_pending_owner_b
):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order = order_pending_owner_b

    with pytest.raises(ResourceNotFound) as exc:
        order_paid_service(
            actor_membership=owner_membership_a,
            order_id=order.id,
        )

    order.refresh_from_db()

    assert order.status == Order.Status.PAID
    assert "order tidak ditemukan" in str(exc.value).lower()


@pytest.mark.django_db
def test_order_paid_service_failed_when_user_is_cashier(
    cashier_membership, tenant_context, order_pending_owner_a
):

    # Arrange
    tenant_context(cashier_membership.tenant_id)

    order = order_pending_owner_a

    with pytest.raises(BusinessRuleViolation):
        order_paid_service(
            actor_membership=cashier_membership,
            order_id=order.id,
        )

    order.refresh_from_db()

    assert order.status == Order.Status.PAID


@pytest.mark.django_db(transaction=True)
def test_order_paid_concurrent_only_one_success(
    owner_membership_a, tenant_context, order_pending_owner_a
):

    # Arrange
    success_results = []
    error_results = []

    order = order_pending_owner_a
    barrier = threading.Barrier(2)

    def run_order_paid():

        close_old_connections()

        tenant_context(owner_membership_a.tenant_id)

        try:
            barrier.wait()


            result = order_paid_service(
                actor_membership=owner_membership_a,
                order_id=order.id,
            )
            success_results.append(result)

        except BusinessRuleViolation as exc:
            error_results.append(exc)

        finally:
            close_old_connections()

    # buat thread
    thread_a = threading.Thread(target=run_order_paid)
    thread_b = threading.Thread(target=run_order_paid)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    order.refresh_from_db()

    assert len(success_results) == 1
    assert len(error_results) == 1

    assert isinstance(error_results[0], BusinessRuleViolation)

    print(f"debug: status = {order.status}")
    assert order.status == Order.Status.PAID
