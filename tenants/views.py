from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, views, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.thread_local import get_current_tenant
from orders.permissions import IsTenantManagerOrOwner
from tenants.models import TenantMembership
from tenants.serializers import StaffCreateSerializer, TenantRegisterSerializer
from tenants.services import (
    current_active_membership,
    get_membership_service,
    patch_staff_service,
    public_onboarding_orchestrator,
    remove_member_from_tenant_service,
    staff_provising_orchestrator,
)

from .serializers import (
    CustomTokenObatinPairSerializer,
    CustomTokenRefreshSerializer,
    StaffMemberSerializer,
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

        tenant_id = get_current_tenant()

        # panggil service (buat naro staff ke tenant saat ini)
        staff_user = staff_provising_orchestrator(
            email=data["email"],
            password=data["password"],
            full_name=data["full_name"],
            role=data["role"],
            current_tenant_id=tenant_id,
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


# class TenantMemberViewSet(viewsets.ReadOnlyModelViewSet):
#     permission_classes = [IsAuthenticated, IsTenantManagerOrOwner]

#     serializer_class = TenantMemberDetailSerializer

#     def get_queryset(self):

#         filter_serializer = TenantMemberFilterSerializer(
#             # ambil data dari url (?=role)
#             data=self.request.query_params
#         )

#         # cek validasi si filter_serializer
#         filter_serializer.is_valid(raise_exception=True)

#         role = filter_serializer.validated_data.get("role")

#         return get_tenant_members(tenant_id=get_current_tenant(), role=role)

#     def get_serializer_class(self):
#         if self.action == "dropdown":
#             return TenantMemberDropdownSerializer
#         return TenantMemberDetailSerializer

#     @action(detail=False, methods=["get"])
#     def dropdown(self, request):
#         # self.list otomatis manggil get_queryset() dan get_serializer_class
#         return self.list(request)


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


class StaffViewSet(viewsets.ModelViewSet):

    # ADA BUG DI URL PATCH-STAFF, KALO PAKE PUT DAN ADA PKNYA KELUAR ROLE DARI SI TENANTMEMBERSHIP ITUU

    # pasang permission
    permission_classes = [IsAuthenticated, IsTenantManagerOrOwner]

    # pasang serializer
    serializer_class = StaffPatchSerializer

    def get_queryset(self):

        return TenantMembership.objects.filter(tenant=get_current_tenant())

    def partial_update(self, request, *args, **kwargs):
        # 1. Ambil object target
        target_membership = self.get_object()

        # 2. Validasi request
        serializer = self.get_serializer(
            target_membership,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        # 3. Panggil service
        updated_membership = patch_staff_service(
            actor=request.user,
            target_membership=target_membership,
            validated_data=serializer.validated_data,
        )

        # 4. Serializer untuk response
        response_serializer = TenantMemberDetailSerializer(updated_membership)

        # 5. Return response
        return Response(response_serializer.data)


# ini class gak jadi dipake
# class ProfileViewSet(mixins.RetrieveModelMixin,
#                      mixins.UpdateModelMixin,
#                      viewsets.GenericViewSet):

#     permission_classes = [IsAuthenticated]

#     serializer_class = ProfilePatchSerializer

#     # override
#     def get_object(self):
#         return self.request.user # ambil object user yang lagi login

#     def partial_update(self, request, *args, **kwargs):

#         # ambil object user
#         user = self.get_object()

#         # validasi request
#         serializer = self.get_serializer(
#             user,
#             data=request.data,
#             partial=True
#         )

#         serializer.is_valid(raise_exception=True)

#         # panggil service
#         updated_user = patch_user_service(
#             user=user,
#             validated_data=serializer.validated_data
#         )

#         # panggil serializer untuk response
#         response_serializer = ProfileDetailSerializer(updated_user)

#         return Response(response_serializer.data)


class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated, IsTenantManagerOrOwner]

    # override
    def delete(self, request, pk, format=None):
        # ambil object target
        target_membership = get_object_or_404(
            TenantMembership, id=pk, tenant_id=get_current_tenant(), left_at=None
        )

        # ambil object actor (pake service mini)
        try:
            actor_membership = current_active_membership(
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
