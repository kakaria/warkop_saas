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

    def validate_name(self, value):
        # ambil object product
        product = self.instance

        # cek apakah product ini ada, belom di arsip, namanya sama (case-insensitive), dan bukan product dirinya sendiri (product ini)
        duplicate_exists = (
            Product.objects.filter(
                tenant_id=product.tenant_id,
                name=value,  # biar "Kopi" = "kopi"
                is_archived=False,
            )
            .exclude(  # kecuali product ini (yang lagi mau di patch)
                id=product.id,
            )
            .exists()
        )

        if duplicate_exists:
            raise serializers.ValidationError("Product has been stored in this tenant!")

        return value
