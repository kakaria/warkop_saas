
import time
import threading

import pytest
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, transaction

from core.exceptions import BusinessRuleViolation
from core.thread_local import set_current_tenant
from orders.dto import VoidOrderDTO
from orders.models import Order
from orders.services import order_void_service
from products.models import Product, ReasonChoices, StockMovement
from products.services import adjust_stock_service


@pytest.mark.django_db
def test_order_void_service_success(
    owner_membership_a, tenant_context, order_pending_owner_a, product
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order_item = order_pending_owner_a.items.get()
    initial_stock = product.stock

    data = VoidOrderDTO(
        reason=ReasonChoices.ORDER_VOID, notes="pesanan tidak sesuai customer"
    )

    order = order_void_service(
        actor_membership=owner_membership_a,
        order_id=order_pending_owner_a.id,
        data=data,
    )

    order.refresh_from_db()

    assert order.status == Order.Status.VOID

    product.refresh_from_db()
    assert product.stock == initial_stock + order_item.quantity

    movement_exists = StockMovement.objects.filter(
        product=product,
        reason=data.reason,
        notes=data.notes,
        action=StockMovement.Action.ADD,
    )

    assert movement_exists.count() == 1

    movement = movement_exists.get()
    assert movement.quantity == order_item.quantity


@pytest.mark.django_db
def test_order_void_service_failed_when_order_status_is_not_pending(
    owner_membership_a,
    tenant_context,
    order_not_pending_owner_a,
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    order_item = order_not_pending_owner_a.items.first()
    initial_stock = order_item.product.stock
    initial_stock_movement = StockMovement.objects.filter(
        product_id=order_item.product_id
    ).count()

    data = VoidOrderDTO(
        reason=ReasonChoices.ORDER_VOID, notes="pesanan tidak sesuai customer"
    )

    with pytest.raises(
        BusinessRuleViolation,
        match="Hanya Order dengan status PENDING yang dapat di-void",
    ):
        order_void_service(
            actor_membership=owner_membership_a,
            order_id=order_not_pending_owner_a.id,
            data=data,
        )

    order_not_pending_owner_a.refresh_from_db()
    order_item.refresh_from_db()

    assert order_not_pending_owner_a.status != Order.Status.VOID

    assert order_item.product.stock == initial_stock

    current_stock_movement = StockMovement.objects.filter(
        product_id=order_item.product.id
    ).count()
    assert current_stock_movement == initial_stock_movement


@pytest.mark.django_db
def test_order_void_service_failed_when_user_is_cashier(
    cashier_membership,
    tenant_context,
    order_not_pending_owner_a,
):
    # Arrange
    tenant_context(cashier_membership.tenant_id)

    order_item = order_not_pending_owner_a.items.first()
    initial_stock = order_item.product.stock
    initial_stock_movement = StockMovement.objects.filter(
        product_id=order_item.product_id
    ).count()

    data = VoidOrderDTO(
        reason=ReasonChoices.ORDER_VOID, notes="pesanan tidak sesuai customer"
    )

    with pytest.raises(
        BusinessRuleViolation,
        match="Anda tidak memiliki",
    ):
        order_void_service(
            actor_membership=cashier_membership,
            order_id=order_not_pending_owner_a.id,
            data=data,
        )

    order_not_pending_owner_a.refresh_from_db()
    order_item.refresh_from_db()

    assert order_not_pending_owner_a.status != Order.Status.VOID

    assert order_item.product.stock == initial_stock

    current_stock_movement = StockMovement.objects.filter(
        product_id=order_item.product.id
    ).count()
    assert current_stock_movement == initial_stock_movement


@pytest.mark.django_db
def test_order_void_service_failed_when_stock_movement_failed_to_create(
    owner_membership_a,
    tenant_context,
    order_pending_owner_a_with_many_product,
    monkeypatch,
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    # ambil semua orderitems
    order_items = list(order_pending_owner_a_with_many_product.items.all())

    # mapping product_id:product_stock
    initial_stocks = {item.product_id: item.product.stock for item in order_items}

    # ambil semua stock_movement dan bikin mapping
    initial_stock_movements = {
        item.product_id: StockMovement.objects.filter(
            product_id=item.product_id
        ).count()
        for item in order_items
    }

    data = VoidOrderDTO(
        reason=ReasonChoices.ORDER_VOID, notes="pesanan tidak sesuai customer"
    )

    # bikin fungsi yang salah
    def fail_bulk_create(*args, **kwargs):
        raise RuntimeError("Stock movement creation failed")

    monkeypatch.setattr(StockMovement.objects, "bulk_create", fail_bulk_create)

    with pytest.raises(RuntimeError):
        order_void_service(
            actor_membership=owner_membership_a,
            order_id=order_pending_owner_a_with_many_product.id,
            data=data,
        )

    order_pending_owner_a_with_many_product.refresh_from_db()

    # Assert

    assert order_pending_owner_a_with_many_product.status == Order.Status.PENDING

    for product_id, initial_stock in initial_stocks.items():
        product = Product.global_objects.get(pk=product_id)

        print(f"product.stock: {product.stock}")

        assert product.stock == initial_stock

    for product_id, current_stock_movement in initial_stock_movements.items():
        stock_movement = StockMovement.objects.filter(product_id=product_id).count()

        assert current_stock_movement == stock_movement


@pytest.mark.django_db(transaction=True)
def test_order_void_service_only_one_succeeds(
    tenant_context, owner_membership_a, order_pending_owner_a, product
):
    # Arrange

    order = order_pending_owner_a
    order_item = order.items.get()

    initial_stock = product.stock

    success_results = []
    error_results = []

    barrier = threading.Barrier(2)

    def run_void_order():
        close_old_connections()

        tenant_context(owner_membership_a.tenant_id)

        try:
            barrier.wait()

            data = VoidOrderDTO(
                reason=ReasonChoices.ORDER_VOID, notes="customer salah memilih pesan"
            )

            result = order_void_service(
                actor_membership=owner_membership_a,
                order_id=order.id,
                data=data,
            )

            success_results.append(result)

        except BusinessRuleViolation as exc:
            error_results.append(exc)

        finally:
            close_old_connections()

    # BIKIN THREAD
    thread_a = threading.Thread(target=run_void_order)
    thread_b = threading.Thread(target=run_void_order)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    order_pending_owner_a.refresh_from_db()

    # assert
    assert len(success_results) == 1
    assert len(error_results) == 1

    assert isinstance(error_results[0], BusinessRuleViolation)

    assert "hanya order" in str(error_results[0]).lower()

    # cek status order
    assert order.status == Order.Status.VOID

    # cek stock movement hanya terjadi 1 kali (yang balikin stock dari quantity order)
    movement = StockMovement.objects.filter(
        product_id=order_item.product.id,
        reason=ReasonChoices.ORDER_VOID,
        action=StockMovement.Action.ADD,
    )
    assert movement.count() == 1

    product.refresh_from_db()
    # cek jumlah stock product udah balik jadi kayak jumlah stock awal
    assert product.stock == initial_stock + order_item.quantity


@pytest.mark.django_db(transaction=True)
def test_concurrent_void_and_stock_adjustment_preserve_product(
    tenant_context, owner_membership_a, order_pending_owner_a, product
):
    # Arrange

    tenant_context(owner_membership_a.tenant_id)

    order = order_pending_owner_a
    order_item = order.items.get()
    initial_stock = product.stock

    success_results = []
    error_results = []
    execute_result = []

    barrier = threading.Barrier(2)

    data = VoidOrderDTO(
        reason=ReasonChoices.ORDER_VOID, notes="customer salah memilih pesan"
    )

    adjustment_data = {
        "action": "DEDUCT",
        "quantity": 5,
        "reason": "SALE",
        "notes": "penyesuaian stock",
    }

    def run_void_order():
        close_old_connections()

        tenant_context(owner_membership_a.tenant_id)

        try:
            barrier.wait()

            result = order_void_service(
                actor_membership=owner_membership_a,
                order_id=order.id,
                data=data,
            )

            execute_result.append("void menang")

            success_results.append(result)

        except BusinessRuleViolation as exc:
            error_results.append(exc)

        finally:
            close_old_connections()

    def stock_adjustment():
        close_old_connections()
        set_current_tenant(owner_membership_a.tenant_id)

        try:
            barrier.wait()
            time.sleep(0.1)

            result = adjust_stock_service(
                actor_membership=owner_membership_a,
                product_id=product.id,
                validated_data=adjustment_data,
            )

            execute_result.append("stock menang")
            success_results.append(result)
        except Exception as exc:
            error_results.append(exc)

        finally:
            close_old_connections()

    # BIKIN THREAD
    thread_void_order = threading.Thread(target=run_void_order)
    thread_stock_adjustment = threading.Thread(target=stock_adjustment)

    thread_void_order.start()
    thread_stock_adjustment.start()

    thread_void_order.join()
    thread_stock_adjustment.join()

    print("hasil balapan")
    print(f"pemenang pertama: {execute_result[0]}")
    print(f"pemenang kedua: {execute_result[1]}")

    # assert
    assert not error_results
    assert len(success_results) == 2

    order.refresh_from_db()

    assert order.status == Order.Status.VOID

    product.refresh_from_db()

    print(f"JUMLAH STOK AKHIR: {product.stock}")
    print(f"quantity: {order_item.quantity}")
    print(f"stock adjustment: {adjustment_data['quantity']}")

    # cek jumlah stock product udah balik ke awal dan dikurang sama adjustment
    assert (
        product.stock
        == initial_stock + order_item.quantity - adjustment_data["quantity"]
    )
