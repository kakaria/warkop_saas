from dataclasses import dataclass


@dataclass(frozen=True)
class OrderItemDTO:
    product_id: int
    quantity: int

    def __init


@dataclass(frozen=True)
class CreateOrderDTO:
    items: list[OrderItemDTO]
