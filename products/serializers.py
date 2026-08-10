from random import choice

from rest_framework import serializers

from products.models import Product, ReasonChoices, StockMovement


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


class StockAdjustmentSerializer(serializers.Serializer):

    action = serializers.ChoiceField(choices=StockMovement.Action.choices)
    quantity = serializers.IntegerField(min_value=1)
    reason = serializers.ChoiceField(choices=ReasonChoices.choices)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate(self, attrs):
        reason = attrs["reason"]
        action = attrs["action"]
        notes = attrs.get("notes", "").strip()

        if reason == ReasonChoices.OTHER and not notes:
            raise serializers.ValidationError(
                "Notes wajib diisi jika reason adalah OTHER!"
            )

        # mapping untuk reason -> action
        expected_actions = {
            ReasonChoices.RESTOCK: StockMovement.Action.ADD,
            ReasonChoices.SALE: StockMovement.Action.DEDUCT,
            ReasonChoices.DAMAGED: StockMovement.Action.DEDUCT,
            ReasonChoices.EXPIRED: StockMovement.Action.DEDUCT,
            ReasonChoices.LOST: StockMovement.Action.DEDUCT,
        }

        expected_action = expected_actions.get(reason)

        # cek reason -> action
        if expected_action is not None and action != expected_action:
            raise serializers.ValidationError(
                f"Reason {reason} hanya dapat digunakan dengan action {expected_action}"
            )

        attrs["notes"] = notes  # dimasukin lagi karena udah pake .strip()
        return attrs
