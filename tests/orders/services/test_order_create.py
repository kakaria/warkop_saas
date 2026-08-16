import threading

import pytest
from django.db import close_old_connections, transaction
from django.db.models import Q

from core.exceptions import InsufficientStockError, ProductNotFoundError
from orders.dto import CreateOrderDTO, OrderItemDTO
from orders.models import Order, OrderItem
from orders.serializers import OrderCreateSerializer
from orders.services import create_order_service
from products.models import StockMovement

# @pytest.mark.django_db
# def test_order_create_serializer_valid_payload(product, productB):
#     serializer = OrderCreateSerializer(
#         data={"items": [{"product_id": product.id, "quantity": 3}]}
#     )

#     assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_create_order_service_success(
    manager_membership, product, productB, productC, tenant_context
):
    # Arrange
    tenant_context(manager_membership.tenant_id)
    initial_stock = 50
    product.stock = initial_stock
    product.save(update_fields=["stock"])

    dto = CreateOrderDTO(
        items=(
            OrderItemDTO(product_id=product.id, quantity=5),
            OrderItemDTO(product_id=productB.id, quantity=5),
            OrderItemDTO(product_id=productC.id, quantity=5),
        )
    )

    # Act
    order = create_order_service(actor_membership=manager_membership, data=dto)

    expected_total = order.total_price

    item = order.items.get(product=product)

    order.refresh_from_db()

    product.refresh_from_db()
    productB.refresh_from_db()
    productC.refresh_from_db()

    # Assert
    assert product.stock == initial_stock - 5
    assert productB.stock == initial_stock - 5
    assert productC.stock == initial_stock - 5
    assert order.items.count() == 3
    assert order.total_price == expected_total
    assert item.price_at_transaction == product.price
    assert (
        StockMovement.objects.filter(
            Q(product_id=product.id)
            | Q(product_id=productB.id)
            | Q(product_id=productC.id)
        ).count()
        == 3
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "scenario_name, stock, is_archived, quantity, expected_error",
    [
        ("insufficient_stock_scenario", 5, False, 10, InsufficientStockError),
        ("product_archived_is_true", 10, True, 5, ProductNotFoundError),
    ],
)
def test_create_order_service_failed(
    manager_membership,
    product,
    tenant_context,
    scenario_name,
    stock,
    is_archived,
    quantity,
    expected_error,
):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    product.stock = stock
    product.is_archived = is_archived
    product.save(update_fields=["stock", "is_archived"])

    dto = CreateOrderDTO(
        items=(OrderItemDTO(product_id=product.id, quantity=quantity),)
    )

    # Act
    with pytest.raises(expected_error):

        create_order_service(actor_membership=manager_membership, data=dto)

    product.refresh_from_db()

    # Assert
    assert product.stock == stock
    assert not StockMovement.objects.filter(product_id=product.id).exists()
    assert not Order.global_objects.filter(
        tenant_id=manager_membership.tenant_id
    ).exists()


@pytest.mark.django_db
def test_create_order_rolls_back_when_stock_movement_creation_fails(
    manager_membership, product, tenant_context, monkeypatch
):

    # Arrange
    tenant_context(manager_membership.tenant_id)
    initial_stock = product.stock

    initial_order_count = Order.global_objects.count()

    assert not Order.objects.filter(tenant_id=manager_membership.tenant_id).exists()
    assert not StockMovement.objects.filter(product_id=product.id).exists()

    dto = CreateOrderDTO(items=(OrderItemDTO(product_id=product.id, quantity=5),))

    def fail_bulk_create(*args, **kwargs):
        raise RuntimeError("Stock movement creation failed")

    monkeypatch.setattr(
        StockMovement.objects,
        "bulk_create",
        fail_bulk_create,
    )

    with pytest.raises(RuntimeError):
        create_order_service(actor_membership=manager_membership, data=dto)

    # Assert
    product.refresh_from_db()

    assert product.stock == initial_stock
    assert Order.global_objects.count() == initial_order_count
    assert not Order.objects.filter(tenant_id=manager_membership.tenant_id).exists()
    assert not OrderItem.objects.filter(product_id=product.id).exists()
    assert not StockMovement.objects.filter(product_id=product.id).exists()


@pytest.mark.django_db(transaction=True)
def test_create_order_concurrency_does_not_oversell(
    tenant_context,
    owner_membership_a,
    product,
):
    # Arrange
    product.stock = 5
    product.save(update_fields=["stock"])

    barrier = threading.Barrier(2)

    success_results = []
    error_results = []

    def create_order(quantity):
        close_old_connections()

        tenant_context(owner_membership_a.tenant_id)

        try:
            barrier.wait()

            dto = CreateOrderDTO(
                items=(OrderItemDTO(product_id=product.id, quantity=quantity),)
            )

            # buat order
            order = create_order_service(actor_membership=owner_membership_a, data=dto)

            success_results.append(order.id)

        except InsufficientStockError as exc:
            error_results.append(exc)

        finally:
            close_old_connections()

    # bikin thread
    thread_a = threading.Thread(
        target=create_order,
        args=(4,),
    )

    thread_b = threading.Thread(
        target=create_order,
        args=(4,),
    )

    # jalanin thread
    thread_a.start()
    thread_b.start()

    # bikin thread utama nunggu thread sampe selesai
    thread_a.join()
    thread_b.join()

    product.refresh_from_db()

    assert len(success_results) == 1
    assert len(error_results) == 1
    assert product.stock == 1
    assert (
        Order.global_objects.filter(tenant_id=owner_membership_a.tenant_id).count() == 1
    )
    assert (
        OrderItem.objects.filter(order__tenant_id=owner_membership_a.tenant_id).count()
        == 1
    )
    assert StockMovement.objects.filter(product_id=product.id).count() == 1
