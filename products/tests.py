from django.db.migrations import serializer
import pytest

from products.models import ReasonChoices, StockMovement
from products.serializers import StockAdjustmentSerializer
from products.services import adjust_stock_service


# UNTUK NGETEST APAKAH VALIDASI DARI PAYLOAD BERJALAN DENGAN BAIK
def test_stock_requires_add():
    serializer = StockAdjustmentSerializer(
        data={
            "action": StockMovement.Action.DEDUCT,
            "quantity": 100,
            "reason": ReasonChoices.ADJUSTMENT,
            "notes": "we need this to be write in",
        }
    )

    assert serializer.is_valid()



def test_validated_adjustment():
    serializer = StockAdjustmentSerializer(
        data = {
            "reason": ReasonChoices.ADJUSTMENT,
            "quantity": 90,
            "target_stock": 100,
            "notes": "salah input seharusnya 90"
        }
    )

    assert serializer.is_valid()


