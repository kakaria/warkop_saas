from dataclasses import dataclass


@dataclass(frozen=True)
class OrderItemDTO:
    product_id: int
    quantity: int

    def __post_init__(self):
        if self.product_id <= 0:
            raise ValueError("Product_id harus lebih dari 0")

        if self.quantity <= 0:
            raise ValueError("Quantity harus lebih dari 0")


@dataclass(frozen=True)
class CreateOrderDTO:
    items: tuple[OrderItemDTO, ...]

    def __post_init__(self):
        if not self.items:
            raise ValueError("Order harus memiliki minimal 1 item")

        product_ids = [item.product_id for item in self.items]

        if len(product_ids) != len(set(product_ids)):
            raise ValueError(
                "Product yang sama tidak boleh muncul lebih dari satu kali."
            )
