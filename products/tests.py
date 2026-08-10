from products.models import ReasonChoices, StockMovement
from products.serializers import StockAdjustmentSerializer


# UNTUK NGETEST APAKAH VALIDASI DARI PAYLOAD BERJALAN DENGAN BAIK
def test_stock_requires_add():
    serializer = StockAdjustmentSerializer(
        data={
            "action": StockMovement.Action.DEDUCT,
            "quantity": 3138012,
            "reason": ReasonChoices.SALE,
        }
    )

    assert serializer.is_valid()
