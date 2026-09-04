from datetime import datetime, timezone

import pytest

from orders.models import Order, OrderItem
from products.models import Product
from reports.services import get_today_product_sales_service


@pytest.mark.django_db
def test_product_sales_service_success_include_zero_sales(
    owner_membership_a, tenant_context, tenantA
):
    # Arrange
    tenant_context(tenantA.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    # bikin product yang terjual hari ini
    product_sold = Product.objects.create(
        tenant_id=tenantA.id,
        name="Kopi Susu",
        price=5000,
        stock=100,
        created_by=owner_membership_a.user,
    )

    # product yang gak terjual
    product_not_sold = Product.objects.create(
        tenant_id=tenantA.id,
        name="Mie Nyemek",
        price=15000,
        stock=10,
        created_by=owner_membership_a.user,
    )

    # bikin order
    order = Order.objects.create(
        tenant_id=tenantA.id,
        created_by=owner_membership_a.user,
        total_price=5000,
        created_at=datetime(2026, 8, 26, 17, 0, tzinfo=timezone.utc),
        status=Order.Status.PAID,
    )

    Order.objects.filter(id=order.id).update(
        created_at=datetime(2026, 8, 26, 17, 00, tzinfo=timezone.utc)
    )

    OrderItem.objects.create(
        order=order,
        product=product_sold,
        product_name_at_transaction="Kopi Susu",
        price_at_transaction=5000,
        quantity=1,
        sub_total=5000,
    )

    result = get_today_product_sales_service(
        actor_membership=owner_membership_a,
        now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
    )

    report = {item["product_id"]: item for item in result}

    assert report[product_sold.id]["quantity_sold"] == 1
    assert report[product_not_sold.id]["quantity_sold"] == 0


@pytest.mark.django_db
def test_product_sales_service_keeps_archived_product_with_sales(
    owner_membership_a, tenant_context, tenantA
):
    # Arrange
    tenant_context(tenantA.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    # bikin product yang terjual hari ini
    product_sold = Product.objects.create(
        tenant_id=tenantA.id,
        name="Kopi Latte",
        price=5000,
        stock=100,
        created_by=owner_membership_a.user,
    )

    # bikin order
    order = Order.objects.create(
        tenant_id=tenantA.id,
        created_by=owner_membership_a.user,
        total_price=5000,
        created_at=datetime(2026, 8, 26, 17, 0, tzinfo=timezone.utc),
        status=Order.Status.PAID,
    )

    Order.objects.filter(id=order.id).update(
        created_at=datetime(2026, 8, 26, 17, 00, tzinfo=timezone.utc)
    )

    order_item = OrderItem.objects.create(
        order=order,
        product=product_sold,
        product_name_at_transaction="Kopi Susu",
        price_at_transaction=5000,
        quantity=1,
        sub_total=5000,
    )

    product_sold.is_archived = True

    product_sold.save(update_fields=["is_archived"])

    result = get_today_product_sales_service(
        actor_membership=owner_membership_a,
        now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
    )

    report = {item["product_id"]: item for item in result}

    assert report[product_sold.id]["quantity_sold"] == 1
    assert (
        report[product_sold.id]["product_name"]
        == order_item.product_name_at_transaction
    )


@pytest.mark.django_db
def test_today_product_sales_is_tenant_scoped(
    owner_membership_a, owner_membership_b, tenant_context, tenantA, tenantB
):
    # Arrange
    tenant_context(tenantB.id)

    tenantA.timezone = "Asia/Jakarta"
    tenantA.save(update_fields=["timezone"])

    tenantB.timezone = "Asia/Jakarta"
    tenantB.save(update_fields=["timezone"])

    # bikin product yang terjual hari ini
    product_sold_a = Product.objects.create(
        tenant_id=tenantA.id,
        name="Kopi Latte",
        price=5000,
        stock=100,
        created_by=owner_membership_a.user,
    )

    product_sold_b = Product.objects.create(
        tenant_id=tenantB.id,
        name="Kopi Latte",
        price=5000,
        stock=100,
        created_by=owner_membership_b.user,
    )

    # bikin order
    order_a = Order.objects.create(
        tenant_id=tenantA.id,
        created_by=owner_membership_a.user,
        total_price=5000,
        created_at=datetime(2026, 8, 26, 17, 0, tzinfo=timezone.utc),
        status=Order.Status.PAID,
    )

    Order.objects.filter(id=order_a.id).update(
        created_at=datetime(2026, 8, 26, 17, 00, tzinfo=timezone.utc)
    )

    order_item_a = OrderItem.objects.create(
        order=order_a,
        product=product_sold_a,
        product_name_at_transaction="Kopi Susu",
        price_at_transaction=5000,
        quantity=1,
        sub_total=5000,
    )

    # bikin order b
    order_b = Order.objects.create(
        tenant_id=tenantB.id,
        created_by=owner_membership_b.user,
        total_price=5000,
        created_at=datetime(2026, 8, 26, 17, 0, tzinfo=timezone.utc),
        status=Order.Status.PAID,
    )

    Order.objects.filter(id=order_b.id).update(
        created_at=datetime(2026, 8, 26, 17, 00, tzinfo=timezone.utc)
    )

    order_item_b = OrderItem.objects.create(
        order=order_b,
        product=product_sold_b,
        product_name_at_transaction="Kopi Susu",
        price_at_transaction=5000,
        quantity=1,
        sub_total=5000,
    )

    result = get_today_product_sales_service(
        actor_membership=owner_membership_b,
        now=datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc),
    )

    product_ids = {item["product_id"] for item in result}

    report = {item["product_id"]: item for item in result}

    assert report[product_sold_b.id]["quantity_sold"] == order_item_b.quantity
    assert product_sold_b.id in product_ids
    assert product_sold_a.id not in product_ids
