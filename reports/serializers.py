from rest_framework import serializers


class TodayProductSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    gross_order_value = serializers.IntegerField()


class TodayStockMovementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_id = serializers.CharField()
    action = serializers.CharField()
    quantity = serializers.IntegerField()
    reason = serializers.CharField()
    notes = serializers.CharField()
    created_by = serializers.IntegerField()
    created_at = serializers.DateTimeField()
