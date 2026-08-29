from datetime import date, datetime, timezone

import pytest

from orders.models import Order
from reports.services import get_today_order_count_service
from tenants.models import Tenant
from tenants.time import get_business_date, get_business_day_boundary
from users.models import User


def test_business_day_boundary():
    start, end = get_business_day_boundary(
        timezone_name="Asia/Jayapura",
        business_date=date(2026, 8, 25),
    )

    assert start == datetime(2026, 8, 24, 15, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 8, 25, 15, 0, tzinfo=timezone.utc)


def test_get_business_date_uses_tenant_timezone():
    now = datetime(
        2026,
        8,
        25,
        17,
        30,
        tzinfo=timezone.utc,
    )

    result = get_business_date(
        timezone_name="Asia/Jakarta",
        now=now,
    )

    assert result == date(2026, 8, 26)


@pytest.mark.django_db
def test_today_order_count_respects_tenant_timezone(
    owner_membership_a,
    tenantA,
    tenant_context,
):

    tenant_context(tenantA.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    owner_membership_a.tenant.refresh_from_db()

    # helper function
    def create_historical_order(dt: datetime):
        order = Order.objects.create(
            tenant=tenantA,
            created_by=owner_membership_a.user,
            total_price=10000,
        )
        Order.objects.filter(id=order.id).update(created_at=dt)

    create_historical_order(datetime(2026, 8, 24, 16, 59, tzinfo=timezone.utc))
    create_historical_order(datetime(2026, 8, 24, 17, 00, tzinfo=timezone.utc))
    create_historical_order(datetime(2026, 8, 25, 16, 59, tzinfo=timezone.utc))
    create_historical_order(datetime(2026, 8, 25, 17, 00, tzinfo=timezone.utc))

    result = get_today_order_count_service(
        actor_membership=owner_membership_a,
        now=datetime(
            2026,
            8,
            26,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert result == 1


@pytest.mark.django_db
def test_today_order_count_is_tenant_scope(
    owner_membership_a, owner_membership_b, tenant_context, tenantA, tenantB
):

    # Arrange

    tenant_context(tenantA.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    owner_membership_a.refresh_from_db()

    tenantB.timezone = "Asia/Jakarta"
    tenantB.save(update_fields=["timezone"])

    owner_membership_b.refresh_from_db()

    # helper function
    def create_historical_order(tenant: Tenant, user: User, dt: datetime):
        order = Order.objects.create(
            tenant=tenant,
            created_by=user,
            total_price=10000,
        )
        Order.objects.filter(id=order.id).update(created_at=dt)

    # create order
    create_historical_order(
        tenantA,
        owner_membership_a.user,
        datetime(2026, 8, 26, 18, 00, tzinfo=timezone.utc),
    )
    create_historical_order(
        tenantB,
        owner_membership_b.user,
        datetime(2026, 8, 26, 18, 00, tzinfo=timezone.utc),
    )

    result = get_today_order_count_service(
        actor_membership=owner_membership_a,
        now=datetime(2026, 8, 27, 10, 00, tzinfo=timezone.utc),
    )

    assert result == 1
