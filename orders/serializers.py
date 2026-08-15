from urllib import request

from django.db.migrations import serializer
from django.views import View
from rest_framework import serializers

from core.thread_local import get_current_tenant
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
        print(f"DEBUG: product_id: {product_ids}")

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Terdapat produk yang sama lebih dari satu kali dalam pesanan."
            )
        return value


# serializer untuk convert data menjadi JSON (output serializer)
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
        fields = ["id", "created_at", "total_price", "items"]
        read_only_fields = fields
