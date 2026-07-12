from rest_framework import serializers

from .models import OrderDetail, Order


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderDetail
        fields = [
            "id",
            "order",
            "product",
            "quantity",
            "product_name_at_transaction",
            "price_at_transaction",
        ]

        read_only_fields = ["product_name_at_transaction", "price_at_transaction"]


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(
        many=True
    )  # ambil data dari pesanan user (kayak bikin kertas kecil (OrderItems) ditaro di map (Order)), many=True itu dia nerima dalam bentuk format List (banyak barang)

    class Meta:
        model = Order
        fields = [
            "id",
            "tenant",
            "items",
            "total_price",
            "status",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "tenant",
            "total_price",
            "status",
            "created_by",
            "created_at",
        ]
