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
            "created_by",
        ]
        read_only_fields = fields


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price"]
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

    action = serializers.ChoiceField(
        choices=StockMovement.Action.choices, required=False
    )
    quantity = serializers.IntegerField(min_value=1, required=False)
    reason = serializers.ChoiceField(choices=ReasonChoices.choices)
    notes = serializers.CharField(max_length=255, required=False, allow_blank=True)
    target_stock = serializers.IntegerField(min_value=0, required=False)

    def validate(self, attrs):

        # field hasil validate
        reason = attrs["reason"]  # wajib ada, kalo gak dikirim KeyError
        action = attrs.get("action")
        quantity = attrs.get("quantity")
        notes = attrs.get("notes", "").strip()

        # ambil target_stock jika reason == Adjustment
        if reason == ReasonChoices.ADJUSTMENT:
            target_stock = attrs.get("target_stock")

            if target_stock is None:
                raise serializers.ValidationError(
                    {"target_stock": "Target Stock harus diisi untuk Adjustment!"}
                )

            # gak boleh ada action waktu pake Adjustment
            if "action" in attrs:
                raise serializers.ValidationError(
                    {"action": "Action tidak boleh diisi untuk Adjustment!"}
                )

            # gak boleh ada quantity saat menggunakan Adjustment
            if "quantity" in attrs:
                raise serializers.ValidationError(
                    {"quantity": "Quantity tidak boleh diisi untuk Adjustment!"}
                )

        # selain Adjustment, harus ada action dan quantity tapi gak boleh ada target_stock
        else:
            if action is None:
                raise serializers.ValidationError({"action": "Action harus diisi!"})
            if quantity is None:
                raise serializers.ValidationError({"quantity": "Quantity harus diisi!"})
            if "target_stock" in attrs:
                raise serializers.ValidationError(
                    {"target_stock": "Target stock dilarang!"}
                )

        # notes harus diisi ketika memilih OTHER atau Adjustment
        if reason in [ReasonChoices.OTHER, ReasonChoices.ADJUSTMENT] and not notes:
            raise serializers.ValidationError({"notes": "Notes wajib diisi!"})

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


class StockMovementDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "product_id",
            "action",
            "quantity",
            "reason",
            "notes",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields
