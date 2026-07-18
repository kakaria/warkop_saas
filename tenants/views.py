from rest_framework import permissions, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.thread_local import get_current_tenant
from orders.permissions import IsTenantManagerOrOwner
from tenants.serializers import StaffCreateSerializer, TenantRegisterSerializer
from tenants.services import (
    get_tenant_members,
    public_onboarding_orchestrator,
    staff_provising_orchestrator,
)

from .serializers import (
    CustomTokenObatinPairSerializer,
    CustomTokenRefreshSerializer,
    StaffMemberSerializer,
    StaffRoleSerializer,
    TenantMemberDetailSerializer,
    TenantMemberDropdownSerializer,
    TenantMemberFilterSerializer,
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

        data = serializer.validated_data

        tenant_id = get_current_tenant()

        # panggil service (buat naro staff ke tenant saat ini)
        staff_user = staff_provising_orchestrator(
            email=data["email"],
            password=data["password"],
            role=data["role"],
            current_tenant_id=tenant_id,
        )

        # response
        return Response(
            {
                "message": f"staf dengan role{data['role']} berhasil ditambahkan",
                "data": {
                    "email": staff_user.email,
                    "role": data["role"],
                },
            },
            status=status.HTTP_201_CREATED,
        )


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenObatinPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    """
    generate token refresh baru dengan hasil inject
    data user di tenant_membership
    """

    serializer_class = CustomTokenRefreshSerializer


class StaffMemberViewSet(viewsets.ReadOnlyModelViewSet):
    # pasang permission
    permission_classes = [IsTenantManagerOrOwner]

    # panggil serializer
    serializer_class = StaffMemberSerializer

    # override function
    def get_queryset(self):
        return get_tenant_staff_list_service()


class StaffRoleViewSet(viewsets.ReadOnlyModelViewSet):

    # pasang permission
    permission_classes = [IsTenantManagerOrOwner]

    # pasang serializer
    serializer_class = StaffRoleSerializer

    # override function
    def get_queryset(self):
        return get_user_role_list_service()


class TenantMemberViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsTenantManagerOrOwner]

    serializer_class = TenantMemberDetailSerializer

    def get_queryset(self):

        filter_serializer = TenantMemberFilterSerializer(
            # ambil data dari url (?=role)
            data=self.request.query_params
        )

        # cek validasi si filter_serializer
        filter_serializer.is_valid(raise_exception=True)

        role = filter_serializer.validated_data.get("role")

        return get_tenant_members(tenant_id=get_current_tenant(), role=role)

    def get_serializer_class(self):
        if self.action == "dropdown":
            return TenantMemberDropdownSerializer
        return TenantMemberDetailSerializer

    @action(detail=False, methods=["get"])
    def dropdown(self, request):
        # self.list otomatis manggil get_queryset() dan get_serializer_class
        return self.list(request)
