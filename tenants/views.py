from rest_framework import permissions, status, views
from rest_framework.response import Response

from orders.permissions import IsTenantManagerOrOwner
from tenants.serializers import StaffCreateSerializer, TenantRegisterSerializer
from tenants.services import (
    public_onboarding_orchestrator,
    staff_provising_orchestrator,
)


class TenantRegisterView(views.APIView):
    """
    pintu gerbang public
    untuk calon OWNER mau daftar Tenant baru
    """

    # izin allowany (siapa aja boleh akses (GET) & daftar (POST))
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # panggil serializer untuk registerOwner
        serializer = TenantRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # hasil validasi kasih ke service layer
        owner_user = public_onboarding_orchestrator(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            tenant_name=serializer.validated_data["tenant_name"],
            tenant_address=serializer.validated_data["tenant_address"],
        )

        # kasih bukti berhasil ke frontend
        return Response(
            {
                "message": "Tenant dan Akun Owner berhasil dibuat",
                "data": {
                    "email": owner_user.email,
                    "tenant_name": serializer.validated_data["tenant_name"],
                    "tenant_address": serializer.validated_data["tenant_address"],
                },
            },
            status=status.HTTP_201_CREATED,
        )


class StaffProvisionView(views.APIView):
    """
    Pintu gerbang internal
    untuk owner/manager nambahin staff baru (cashier/manager) ke tenant mereka
    """

    permission_classes = [IsTenantManagerOrOwner]

    def post(self, request, *args, **kwargs):
        # panggil serializer
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # panggil service (buat naro staff ke tenant saat ini)
        staff_user = staff_provising_orchestrator(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            role=serializer.validated_data["role"],
        )

        # response
        return Response(
            {
                "message": f"staf dengan role{serializer.validated_data['role']} berhasil ditambahkan",
                "data": {
                    "email": staff_user.email,
                    "role": serializer.validated_data["role"],
                },
            },
            status=status.HTTP_201_CREATED,
        )
