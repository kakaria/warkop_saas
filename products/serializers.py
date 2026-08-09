from rest_framework import serializers

from products.models import Product


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    price = serializers.IntegerField(min_value=0)
    stock = serializers.IntegerField(min_value=0)


class ProductDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "price",
            "stock",
            "is_archived",
            "created_at",
        ]
        read_only_fields = fields


class ProductBasicPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "name",
            "price",
        ]
