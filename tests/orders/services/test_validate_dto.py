import pytest

from orders.dto import OrderItemDTO


# test stateless (gak perlu database)
@pytest.mark.parametrize(
    "invalid_id, invalid_quantity, expected_error",
    [
        (-1, 5, ValueError),
        (1, -2, ValueError),
    ],
)
def test_order_item_dto_blocks_invalid_data(
    invalid_id, invalid_quantity, expected_error
):
    # langsung Act
    with pytest.raises(expected_error) as exc_info:
        OrderItemDTO(product_id=invalid_id, quantity=invalid_quantity)

    assert "lebih dari" in str(exc_info.value).lower()
