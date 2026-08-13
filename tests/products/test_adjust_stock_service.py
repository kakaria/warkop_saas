import threading

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, close_old_connections

from core.exceptions import (
    InsufficientStockError,
    ProductNotFoundError,
    StockMovementCreationError,
)
from products.models import Product, ReasonChoices, StockMovement
from products.services import adjust_stock_service


@pytest.mark.django_db
def test_adjust_stock_add_success(manager_membership, product, tenant_context):

    tenant_context(manager_membership.tenant_id)

    initial_stock = product.stock
    quantity = 50

    validated_data = {
        "action": StockMovement.Action.ADD,
        "quantity": quantity,
        "reason": ReasonChoices.RESTOCK,
        "notes": "Restock dari supplier",
    }

    movement = adjust_stock_service(
        actor_membership=manager_membership,
        product_id=product.id,
        validated_data=validated_data,
    )

    product.refresh_from_db()
    movement.refresh_from_db()
    print(f"hasil akhir stock product: {product.stock}")

    assert product.stock == initial_stock + quantity
    assert movement.product_id == product.id
    assert movement.action == StockMovement.Action.ADD
    assert movement.quantity == quantity
    assert movement.reason == ReasonChoices.RESTOCK
    assert movement.notes == "Restock dari supplier"
    assert movement.created_by == manager_membership.user


@pytest.mark.django_db
def test_adjust_stock_add_failed(manager_membership, product, tenant_context):

    tenant_context(manager_membership.tenant_id)

    initial_stock = product.stock
    quantity = -10

    validated_data = {
        "action": StockMovement.Action.ADD,
        "quantity": quantity,
        "reason": ReasonChoices.RESTOCK,
        "notes": "",
    }

    with pytest.raises(IntegrityError):
        movement = adjust_stock_service(
            actor_membership=manager_membership,
            product_id=product.id,
            validated_data=validated_data,
        )

    product.refresh_from_db()
    print(f"hasil akhir stock product: {product.stock}")

    assert product.stock == initial_stock


@pytest.mark.django_db
def test_adjust_stock_deduct_success(owner_membership_a, product, tenant_context):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)
    initial_stock = product.stock
    quantity = 5

    # Act
    validated_data = {
        "action": StockMovement.Action.DEDUCT,
        "quantity": quantity,
        "reason": ReasonChoices.SALE,
        "notes": "Sale dari customer",
    }

    movement = adjust_stock_service(
        actor_membership=owner_membership_a,
        product_id=product.id,
        validated_data=validated_data,
    )

    product.refresh_from_db()
    movement.refresh_from_db()
    print(f"hasil akhir stock product: {product.stock}")

    # Assert
    assert product.stock == initial_stock - quantity
    assert movement.product_id == product.id
    assert movement.action == StockMovement.Action.DEDUCT
    assert movement.quantity == quantity
    assert movement.reason == ReasonChoices.SALE
    assert movement.notes == "Sale dari customer"
    assert movement.created_by == owner_membership_a.user


@pytest.mark.django_db
def test_cashier_can_deduct_for_sale(cashier_membership, product, tenant_context):

    # Arrange
    tenant_context(cashier_membership.tenant_id)

    print(f"DEBUG: TENANT_ID CASHIER: {cashier_membership.tenant_id}")
    initial_stock = product.stock
    quantity = 3

    # Act
    validated_data = {
        "reason": ReasonChoices.SALE,
        "quantity": quantity,
        "action": StockMovement.Action.DEDUCT,
        "notes": "",
    }

    movement = adjust_stock_service(
        actor_membership=cashier_membership,
        product_id=product.id,
        validated_data=validated_data,
    )

    product.refresh_from_db()
    movement.refresh_from_db()

    # Assert
    assert product.stock == initial_stock - quantity
    assert StockMovement.objects.filter(
        product=product,
        reason=ReasonChoices.SALE,
    )


@pytest.mark.django_db
def test_cashier_cannot_restock(cashier_membership, product, tenant_context):

    # Arrange
    tenant_context(cashier_membership.tenant_id)

    print(f"DEBUG: TENANT_ID CASHIER: {cashier_membership.tenant_id}")
    initial_stock = product.stock
    quantity = 3

    # Act
    validated_data = {
        "reason": ReasonChoices.RESTOCK,
        "quantity": quantity,
        "action": StockMovement.Action.ADD,
        "notes": "",
    }

    with pytest.raises(PermissionDenied):

        movement = adjust_stock_service(
            actor_membership=cashier_membership,
            product_id=product.id,
            validated_data=validated_data,
        )

        product.refresh_from_db()
        movement.refresh_from_db()

        # Assert
        assert product.stock == initial_stock
        assert not StockMovement.objects.filter(
            product=product,
            reason=ReasonChoices.RESTOCK,
        )


@pytest.mark.django_db
def test_owner_tenant_a_cannot_adjust_stock_tenant_b(
    owner_membership_a, productB, tenant_context
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    print(f"DEBUG: tenant_id dari tenant_a: {owner_membership_a.tenant_id}")
    print(f"DEBUG: tenant_id dari product_b: {productB.tenant_id}")
    initial_stock = productB.stock
    quantity = 10

    # Act
    validated_data = {
        "reason": ReasonChoices.RESTOCK,
        "quantity": quantity,
        "action": StockMovement.Action.ADD,
        "notes": "",
    }

    with pytest.raises(ProductNotFoundError):
        adjust_stock_service(
            actor_membership=owner_membership_a,
            product_id=productB.id,
            validated_data=validated_data,
        )

    print(f"DEBUG: stock awal: {productB.stock}")
    productB.refresh_from_db()

    print(f"DEBUG: stock akhir: {productB.stock}")

    # Assert
    assert productB.stock == initial_stock
    assert not StockMovement.objects.filter(
        product_id=productB.id,
        reason=ReasonChoices.RESTOCK,
    ).exists()


@pytest.mark.django_db
def test_ajdust_stock_rolls_back_when_movement_creation_fails(
    manager_membership,
    product,
    tenant_context,
    monkeypatch,
):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    initial_stock = product.stock
    quantity = 10

    validated_data = {
        "action": StockMovement.Action.DEDUCT,
        "quantity": quantity,
        "reason": ReasonChoices.SALE,
        "notes": "",
    }

    def failed_create(*args, **kwargs):
        raise StockMovementCreationError("Gagal membuat StockMovement")

    monkeypatch.setattr(
        StockMovement.objects,
        "create",
        failed_create,
    )

    # Act
    with pytest.raises(StockMovementCreationError):
        adjust_stock_service(
            actor_membership=manager_membership,
            product_id=product.id,
            validated_data=validated_data,
        )

    product.refresh_from_db()

    assert product.stock == initial_stock
    assert not StockMovement.objects.filter(
        product=product,
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_deduct_cannot_oversell(
    manager_membership,
    product,
    tenant_context,
):
    product.stock = 10
    product.save(update_fields=["stock"])

    tenant_id = manager_membership.tenant_id
    product_id = product.id

    validated_data = {
        "action": StockMovement.Action.DEDUCT,
        "quantity": 7,
        "reason": ReasonChoices.SALE,
        "notes": "",
    }

    # Act
    barrier = threading.Barrier(2)
    results = []

    def worker():
        close_old_connections()

        try:
            tenant_context(tenant_id)
            barrier.wait()

            movement = adjust_stock_service(
                actor_membership=manager_membership,
                product_id=product_id,
                validated_data=validated_data,
            )

            results.append(("success", movement.id))

        except ValidationError:
            results.append(("failed", None))

        finally:
            close_old_connections()

    thread_a = threading.Thread(target=worker)
    thread_b = threading.Thread(target=worker)

    thread_a.start()
    thread_b.start()

    thread_a.join()
    thread_b.join()

    product.refresh_from_db()

    assert product.stock == 3
    assert len(results) == 2

    assert sum(result[0] == "success" for result in results) == 1

    assert sum(result[0] == "failed" for result in results) == 1

    assert (
        StockMovement.objects.filter(
            product=product,
            action=StockMovement.Action.DEDUCT,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_adjust_stock_adjustment_decrease(manager_membership, product, tenant_context):
    tenant_context(manager_membership.tenant_id)

    product.stock = 50
    product.save(update_fields=["stock"])

    validated_data = {
        "reason": ReasonChoices.ADJUSTMENT,
        "target_stock": 20,
        "notes": "Salah input stock, harusnya 20",
    }

    movement = adjust_stock_service(
        actor_membership=manager_membership,
        product_id=product.id,
        validated_data=validated_data,
    )

    product.refresh_from_db()

    assert product.stock == 20
    assert movement.product_id == product.id
    assert movement.action == StockMovement.Action.DEDUCT
    assert movement.quantity == 30
    assert (
        StockMovement.objects.filter(
            product_id=product.id,
            reason=ReasonChoices.ADJUSTMENT,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_adjust_stock_adjustment_increase(manager_membership, product, tenant_context):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    product.stock = 20
    product.save(update_fields=["stock"])

    validated_data = {
        "reason": ReasonChoices.ADJUSTMENT,
        "target_stock": 50,
        "notes": "Salah input stock barang harusnya 50",
    }

    # Act
    movement = adjust_stock_service(
        actor_membership=manager_membership,
        product_id=product.id,
        validated_data=validated_data,
    )

    product.refresh_from_db()

    assert product.stock == 50
    assert movement.product_id == product.id
    assert movement.action == StockMovement.Action.ADD
    assert StockMovement.objects.filter(
        product_id=product.id,
        reason=ReasonChoices.ADJUSTMENT
    ).count() == 1


@pytest.mark.django_db
def test_adjust_stock_adjustment_failed(manager_membership, product, tenant_context):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    product.stock = 20
    product.save(update_fields=["stock"])

    validated_data = {
        "reason": ReasonChoices.ADJUSTMENT,
        "target_stock": 20,
        "notes": "Salah input stock barang harusnya 50",
    }

    # Act
    with pytest.raises(ValidationError):
        movement = adjust_stock_service(
            actor_membership=manager_membership,
            product_id=product.id,
            validated_data=validated_data,
        )

    product.refresh_from_db()

    assert product.stock == 20
    assert not (
        StockMovement.objects.filter(
            product_id=product.id, reason=ReasonChoices.ADJUSTMENT
        ).count()
        == 1
    )
