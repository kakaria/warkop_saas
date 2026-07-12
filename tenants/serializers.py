from rest_framework import serializers
from django.contrib.auth import get_user_model

from tenants.models import TenantMembership

User = get_user_model()


class TenantRegisterSerializer(serializers.Serializer):
    """
        SERIALIZER untuk validasi USER + TENANT
        user pasti owner dan tenant akan baru
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_name = serializers.CharField(max_length=100)
    tenant_address = serializers.CharField(max_length=100)

    # validasi email
    def validate_email(self, value):
        if User.objects.filter(email=value).exists(): # pake .exist() biar cepet
            raise serializers.ValidationError(f"email {value} udah terdaftar bro!")
        return value


class StaffCreateSerializer(serializers.Serializer):
    """
        SERIALIZER untuk VALIDASI USER baru
        USER antara MANAGER atau CASHIER
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[TenantMembership.Role.MANAGER, TenantMembership.Role.CASHIER]
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"email staf {value} udah ada bro!")
        return value
