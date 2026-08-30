from urllib import request

from django.db.migrations import serializer
from django.views import View
from rest_framework import serializers

from core.thread_local import get_current_tenant
from orders.dto import VoidOrderDTO
from products.models import ReasonChoices

# from orders.services import create_order_service
from .models import Order, OrderItem

# class OrderItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OrderDetail
#         fields = [
#             "id",
#             "order",
#             "product",
#             "quantity",
#             "product_name_at_transaction",
#             "price_at_transaction",
#         ]

#         read_only_fields = ["product_name_at_transaction", "price_at_transaction"]


# class OrderCreateSerializer(serializers.ModelSerializer):
#     items = OrderItemSerializer(
#         many=True
#     )  # ambil data dari pesanan user (kayak bikin kertas kecil (OrderItems) ditaro di map (Order)), many=True itu dia nerima dalam bentuk format List (banyak barang)

#     class Meta:
#         model = Order
#         fields = [
#             "id",
#             "tenant",
#             "items",
#             "total_price",
#             "status",
#             "created_by",
#             "created_at",
#         ]
#         read_only_fields = [
#             "tenant",
#             "total_price",
#             "status",
#             "created_by",
#             "created_at",
#         ]


# serializer untuk use case (transaction)
class OrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(
        min_value=1
    )  # biar gak ada yang product_id: -10 (malformed)
    quantity = serializers.IntegerField(min_value=1)  # biar gak ada quantity: 0


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemInputSerializer(
        many=True,
        allow_empty=False,  # biar kalo gak ada items, gak perlu masuk ke services.py
    )

    def validate_items(self, value):
        # cek duplicate product
        product_ids = [item["product_id"] for item in value]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Terdapat produk yang sama lebih dari satu kali dalam pesanan."
            )
        return value


class OrderItemDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "product_name_at_transaction",
            "price_at_transaction",
            "quantity",
            "sub_total",
        ]
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemDetailSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = ["id", "status", "created_at", "created_by", "total_price", "items"]
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "status", "created_at"]
        read_only_fiels = fields


# serializer input void order
class OrderVoidSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=[ReasonChoices.ORDER_VOID])

    notes = serializers.CharField(
        max_length=255,
        required=True,
        allow_blank=False,
    )

    def create_void(self) -> VoidOrderDTO:
        return VoidOrderDTO(
            reason=self.validated_data["reason"],
            notes=self.validated_data["notes"],
        )


class OrderPaidSerializer(serializers.Serializer):
    pass
