from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.tokens import AccessToken

from tenants.models import TenantMembership
from tenants.services import get_user_tenant_claim_service

User = get_user_model()


class TenantRegisterSerializer(serializers.Serializer):
    """
    SERIALIZER untuk validasi USER + TENANT
    user pasti owner dan tenant akan baru
    """

    # validasi field user yang masuk
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    # validasi tenant yang masuk
    tenant_name = serializers.CharField(max_length=100)
    tenant_address = serializers.CharField(max_length=100)

    # validasi email
    def validate_email(self, value):
        if User.objects.filter(
            email=value
        ).exists():  # kalo udah ada email yang user input
            raise serializers.ValidationError(
                f"sory cuy! email: {value}, udah ada yang make"
            )
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


class CustomTokenObatinPairSerializer(TokenObtainPairSerializer):
    """
    bikin KTP
    """

    @classmethod
    def get_token(cls, user):
        # 1. minta token dasar dari simpleJWT
        token = super().get_token(user)

        # 2. suntik data standar
        token["email"] = user.email

        # 3. panggil service untuk panggil datanya
        tenant_claims = get_user_tenant_claim_service(user)

        # 4. masukin dta dari service ke token (convet & validating)
        token["tenant_id"] = tenant_claims["tenant_id"]
        token["tenant_name"] = tenant_claims["tenant_name"]
        token["role"] = tenant_claims["role"]

        return token


# buat custom token refersh
class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Bikin ulang refresh token
    ambil refresh token lama, validasi
    """

    def validate(self, attrs):
        # 1. validasi standard JWT (cek expired / blacklist)
        data = super().validate(attrs)

        # 2. ambil refersh token dari request
        refresh = self.token_class(attrs["refresh"])

        # 3. ambil ID user dari refresh token yang dikrim
        user_id = refresh.payload.get("user_id")
        user = User.objects.get(id=user_id)

        # 4. ambil data tenant_membership si user, biar kalo naik jabatan, role terbaru bakal diinject ke token baru tanpa harus login ulang
        tenant_claim = get_user_tenant_claim_service(user)

        # 5. bikin Access token baru & inject data terbaru dari tenant_claim
        access_token = AccessToken.for_user(user)  # noqa: F821
        access_token["email"] = user.email
        access_token["tenant_id"] = tenant_claim["tenant_id"]
        access_token["tenant_name"] = tenant_claim["tenant_name"]
        access_token["role"] = tenant_claim["role"]

        # 6. ganti token polos pabrik dengan custom token
        data["access"] = str(access_token)

        return data


# nama class gak boleh pake kata verb (harus kata benda tunggal)
class StaffMemberSerializer(serializers.ModelSerializer):
    """
    untuk nampilin data profil staff
    """

    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "email", "role"]


class StaffRoleSerializer(serializers.ModelSerializer):

    # fields yang divalidasi
    email = serializers.EmailField(source="user.email")

    class Meta:
        model = TenantMembership
        fields = ["email", "role"]
        read_only_fields = ["email", "role"]


class TenantMemberFilterSerializer(
    serializers.Serializer
):  # buat validasi filter parameter
    role = serializers.ChoiceField(
        choices=TenantMembership.Role.choices,
        required=False,
    )


# validasi data yang dikirim dan yagn bakal ditampilin
class TenantMemberDetailSerializer(serializers.ModelSerializer):

    # ambil field yang bukan dari table TenantMembership
    email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)

    class Meta:
        model = TenantMembership
        fields = ["id", "user_id", "user_full_name", "email", "tenant_name", "role"]


# SERIALIZER UNTUK PATCH
class StaffPatchSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        required=False, choices=TenantMembership.Role.choices
    )

    class Meta:
        model = TenantMembership
        fields = ["role"]


