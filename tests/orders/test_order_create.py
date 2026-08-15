import pytest

from orders.dto import CreateOrderDTO, OrderItemDTO
from orders.serializers import OrderCreateSerializer
from orders.services import create_order_service


@pytest.mark.django_db
def test_order_create_serializer_valid_payload(product, productB):
    serializer = OrderCreateSerializer(
        data={"items": [{"product_id": product.id, "quantity": 3}]}
    )

    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_create_order_service_success(manager_membership, product, tenant_context):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    dto = CreateOrderDTO(items=[OrderItemDTO(product_id=product.id, quantity=0)])

    print(f"ini dto: {dto}")
    # Act
    order = create_order_service(actor_membership=manager_membership, data=dto)

    # Assert
    assert order.total_price == product.price * 4
