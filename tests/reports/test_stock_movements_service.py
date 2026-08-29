from datetime import datetime, timezone

import pytest

from core.exceptions import BusinessRuleViolation
from products.models import ReasonChoices, StockMovement
from reports.services import get_today_stock_movement_service


@pytest.mark.django_db
def test_report_stock_movement_when_user_is_valid(
    owner_membership_a, tenant_context, tenantA, product
):

    tenant_context(owner_membership_a.tenant_id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    # bikin movement
    movement = StockMovement.objects.create(
        product_id=product.id,
        action=StockMovement.Action.ADD,
        quantity=5,
        reason=ReasonChoices.RESTOCK,
        created_by=owner_membership_a.user,
    )

    StockMovement.objects.filter(id=movement.id).update(
        created_at=datetime(2026, 8, 26, 18, 00, tzinfo=timezone.utc)
    )

    result = get_today_stock_movement_service(
        actor_membership=owner_membership_a,
        now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
    )

    assert len(result) == 1
    assert result[0]["reason"] == movement.reason
    assert result[0]["product_id"] == product.id
    assert result[0]["quantity"] == movement.quantity


@pytest.mark.django_db
def test_report_stock_movement_failed_when_user_is_cashier(
    cashier_membership,
    tenant_context,
):

    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        get_today_stock_movement_service(
            actor_membership=cashier_membership,
            now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
        )


@pytest.mark.django_db
def test_report_stock_movement_respect_timezone_and_tenant_scope(
    owner_membership_a,
    owner_membership_b,
    tenant_context,
    tenantA,
    tenantB,
    product,
    productD,
):

    tenant_context(tenantA.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    tenantB.timezone = "Asia/Jakarta"
    tenantB.save(update_fields=["timezone"])

    def create_historical_movement(product, user, dt):
        movement = StockMovement.objects.create(
            product_id=product.id,
            reason=ReasonChoices.RESTOCK,
            action=StockMovement.Action.ADD,
            quantity=5,
            created_by=user,
        )

        StockMovement.objects.filter(id=movement.id).update(created_at=dt)

        return movement

    create_historical_movement(
        product=product,
        user=owner_membership_a.user,
        dt=datetime(2026, 8, 25, 17, 0, tzinfo=timezone.utc),
    )

    movement_a_in = create_historical_movement(
        product=product,
        user=owner_membership_a.user,
        dt=datetime(2026, 8, 26, 17, 0, tzinfo=timezone.utc),
    )

    create_historical_movement(
        product=productD,
        user=owner_membership_b.user,
        dt=datetime(2026, 8, 25, 18, 0, tzinfo=timezone.utc),
    )

    result = get_today_stock_movement_service(
        actor_membership=owner_membership_a,
        now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
    )

    movement_ids = {item["id"] for item in result}

    assert len(result) == 1
    assert movement_a_in.id in movement_ids
