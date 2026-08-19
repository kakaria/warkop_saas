from dataclasses import dataclass


@dataclass(frozen=True)
class CreateProductDTO:
    name: str
    price: int
    stock: int

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Nama product harus diisi!")
        if self.price < 0:
            raise ValueError("Harga product tidak boleh negatif")
        if self.stock < 0:
            raise ValueError("Stock tidak boleh negatif")
