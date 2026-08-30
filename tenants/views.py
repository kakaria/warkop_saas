from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, views, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.thread_local import get_current_tenant
from tenants.models import TenantMembership
from tenants.permissions import (
    IsAuthenticatedAndHasTenant,
    IsTenantManagerOrOwner,
    IsTenantOwner,
)
from tenants.serializers import (
    StaffCreateSerializer,
    TenantRegisterSerializer,
    TenantTimezonePatchSerializer,
)
from tenants.services import (
    get_current_active_membership,
    get_membership_service,
    patch_staff_service,
    public_onboarding_orchestrator,
    remove_member_from_tenant_service,
    staff_provising_orchestrator,
    update_tenant_timezone_service,
)

from .serializers import (
    AdminTenantMemberDetailSerializer,
    CustomTokenObatinPairSerializer,
    CustomTokenRefreshSerializer,
    StaffPatchSerializer,
    StaffRoleSerializer,
    TenantMemberDetailSerializer,
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
            full_name=serializer.validated_data["full_name"],
            tenant_name=serializer.validated_data["tenant_name"],
            tenant_address=serializer.validated_data["tenant_address"],
        )

        # kasih bukti berhasil ke frontend
        return Response(
            {
                "message": "Tenant dan Akun Owner berhasil dibuat",
                "data": {
                    "email": owner_user.email,
                    "full_name": owner_user.full_name,
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

        # ambil membership dari user yang lagi login
        actor = get_current_active_membership(
            user=request.user,
            tenant_id=get_current_tenant(),
        )
        print(actor.id)

        # panggil service (buat naro staff ke tenant saat ini)
        staff_user = staff_provising_orchestrator(
            actor_membership=actor,
            email=data["email"],
            password=data["password"],
            full_name=data["full_name"],
            role=data["role"],
            current_tenant_id=get_current_tenant(),
        )

        # response
        return Response(
            {
                "message": f"staf dengan role{data['role']} berhasil ditambahkan",
                "data": {
                    "email": staff_user.email,
                    "full_name": staff_user.full_name,
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


class AdminViewMember(viewsets.ReadOnlyModelViewSet):

    serializer_class = AdminTenantMemberDetailSerializer

    # override function
    def get_queryset(self):
        return TenantMembership.objects_global.all()


class StaffRoleViewSet(viewsets.ReadOnlyModelViewSet):

    # pasang permission
    permission_classes = [IsTenantManagerOrOwner]

    # pasang serializer
    serializer_class = StaffRoleSerializer

    # override function
    def get_queryset(self):
        return get_user_role_list_service()


class TenantMemberViewSet(viewsets.ReadOnlyModelViewSet):

    # panggil permission
    permission_classes = [IsAuthenticated, IsTenantManagerOrOwner]

    # panggil serializer
    serializer_class = TenantMemberDetailSerializer

    # override
    def get_queryset(self):
        # panggil serializer buat filter parameter
        filter_serializer = TenantMemberFilterSerializer(
            data=self.request.query_params  # ambil data dari input url (?=role)
        )
        # udah dapet datanya, kita validasi
        filter_serializer.is_valid(raise_exception=True)

        # baca value role dari filter_serializer
        role = filter_serializer.validated_data.get("role")

        # panggil si service
        return get_membership_service(tenant_id=get_current_tenant(), role=role)


class StaffPatchAPIView(APIView):

    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def patch(self, pk, request):
        input_serializer = StaffPatchSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=get_current_tenant(),
        )

        target_membership = get_object_or_404(
            TenantMembership, pk=pk, tenant_id=get_current_tenant()
        )

        patch_staff = patch_staff_service(
            actor_membership=actor_membership,
            target_membership=target_membership,
            validated_data=validated_data,
        )

        output_serializer = TenantMemberDetailSerializer(patch_staff)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    # override
    def delete(self, request, pk, format=None):
        # ambil object target
        target_membership = get_object_or_404(
            TenantMembership, id=pk, tenant_id=get_current_tenant(), left_at=None
        )

        # ambil object actor (pake service mini)
        try:
            actor_membership = get_current_active_membership(
                user=request.user,
                tenant_id=get_current_tenant(),
            )
            print(actor_membership)
        except TenantMembership.DoesNotExist:
            raise NotFound("Membership tidak ditemukan")

        # panggil service
        remove_member_from_tenant_service(
            actor_membership_id=actor_membership.id,
            target_membership_id=target_membership.id,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class TenantPatchTimezoneAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantOwner]

    def patch(self, request):
        input_serializer = TenantTimezonePatchSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        # ambil actor membership
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        data = input_serializer.to_dto()

        # panggil service
        tenant = update_tenant_timezone_service(
            actor_membership=actor_membership, data=data
        )

        return Response({"timezone": tenant.timezone}, status=status.HTTP_200_OK)
