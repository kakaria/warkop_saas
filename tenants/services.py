from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.exceptions import BusinessRuleViolation, ResourceNotFound
from tenants.dto import UpdateTimezoneDTO
from tenants.models import Tenant, TenantMembership
from users.models import User
from users.services import create_user_account_service


def create_tenant_service(*, name: str, address: str) -> Tenant:
    """
    bikin tenant baru
    """
    return Tenant.objects.create(name=name, address=address)


def assign_user_to_tenant_service(
    user: User, tenant: Tenant, role: str
) -> TenantMembership:
    """
    SAMBUNGIN USER KE TENANT lewat model TENANTMEMBERSHIP
    """

    return TenantMembership.objects_global.create(user=user, tenant=tenant, role=role)


def public_onboarding_orchestrator(
    email: str, password: str, full_name: str, tenant_name: str, tenant_address: str
) -> User:
    """
    create new Owner, Tenant, and connect them to TenantMembership
    """

    with transaction.atomic():

        # bikin users
        new_user = create_user_account_service(
            email=email,
            password=password,
            full_name=full_name,
        )

        # bikin tenant dari user diatas
        new_tenant = create_tenant_service(name=tenant_name, address=tenant_address)

        # sambungin new_user & new_tenant pake TenantMembership
        assign_user_to_tenant_service(
            user=new_user,
            tenant=new_tenant,
            role=TenantMembership.Role.OWNER,
        )

        return new_user


def staff_provising_orchestrator(
    actor_membership: TenantMembership,
    email: str,
    password: str,
    full_name: str,
    role: str,
) -> User:
    """
    for assign new member to tenant
    """

    # authorization
    if actor_membership.role not in [
        TenantMembership.Role.OWNER,
        TenantMembership.Role.MANAGER,
    ]:
        raise BusinessRuleViolation("Maaf, kamu tidak bisa membuat member baru")

    # kalo actor_membership is Manager (cuma bisa bikin kasir)
    if actor_membership.role == TenantMembership.Role.MANAGER:
        if role != TenantMembership.Role.CASHIER:
            raise BusinessRuleViolation("Maaf, Manager hanya bisa membuat member Kasir")

    # ambil object Tenant
    tenant_obj = Tenant.objects.get(id=actor_membership.tenant_id)

    # bikin usernya dulu
    staff_user = create_user_account_service(
        email=email, password=password, full_name=full_name
    )

    # taro staff_user di tenant yang sesuai
    assign_user_to_tenant_service(user=staff_user, tenant=tenant_obj, role=role)

    return staff_user


def get_user_tenant_claim_service(user) -> dict:
    """
    AMBIL DATA TENANT AKTIF MILIK USER,
    return dict
    """

    membership = (
        TenantMembership.objects_global.filter(user=user)
        .select_related("tenant")
        .first()
    )

    if membership and membership.tenant:
        return {
            "tenant_id": str(membership.tenant.id),
            "tenant_name": membership.tenant.name,
            "role": membership.role,
            "left_at": membership.left_at,
        }

    return {"tenant_id": None, "tenant_name": None, "role": None}


def get_membership_list_service(
    actor_membership: TenantMembership, role: str | None = None
) -> QuerySet[TenantMembership]:

    # authorization
    if actor_membership.role not in [
        TenantMembership.Role.OWNER,
        TenantMembership.Role.MANAGER,
    ]:
        raise BusinessRuleViolation("Anda tidak memiliki hak untuk melakukan ini!")

    # bikin querynya
    queryset = (
        TenantMembership.objects.filter(
            tenant_id=actor_membership.tenant_id, left_at__isnull=True
        )
        .select_related("user", "tenant")
        .order_by("user")
    )

    # kalo role diisi (cari berdasarkan role)
    if role:
        queryset = queryset.filter(role=role)

    return queryset


def patch_staff_service(
    actor_membership: TenantMembership,
    target_membership: TenantMembership,
    validated_data: dict,
) -> TenantMembership:

    # authorization
    if actor_membership.left_at is not None:
        raise BusinessRuleViolation("Anda bukan member aktif")

    if actor_membership.tenant_id != target_membership.tenant_id:
        raise BusinessRuleViolation("Anda tidak memiliki hak melakukan itu!")

    if actor_membership.role != TenantMembership.Role.OWNER:
        raise BusinessRuleViolation("Anda tidak memiliki hak untuk melakukan itu!")

    # variable kalo id actor dan target sama
    is_self_edit = actor_membership.id == target_membership.id

    # ambil key dari dict validated_data
    new_role = validated_data.get("role")

    # cek kalo owner mau ngedit dirinya sendiri
    if is_self_edit and new_role in [
        TenantMembership.Role.MANAGER,
        TenantMembership.Role.CASHIER,
    ]:
        raise BusinessRuleViolation("Anda tidak boleh menurunkan jabatan anda sendiri")

    if not new_role or target_membership.role == new_role:
        return target_membership

    # apply perubahan
    for key, value in validated_data.items():
        setattr(target_membership, key, value)

    # simpen ke database, pake update_fields
    target_membership.save(update_fields=list(validated_data.keys()))

    return target_membership


def remove_member_from_tenant_service(
    actor_membership: TenantMembership, target_membership_id: int
) -> None:  # karena delete gak ngembaliin apapun

    with transaction.atomic():

        # ambil target_membership
        try:
            target_membership = TenantMembership.objects.select_for_update().get(
                id=target_membership_id,
                tenant_id=actor_membership.tenant_id,
            )

        except TenantMembership.DoesNotExist:
            raise BusinessRuleViolation("Member tidak ditemukan")

        # cek apakah dia selain owner dan manager
        if actor_membership.role not in [
            TenantMembership.Role.OWNER,
            TenantMembership.Role.MANAGER,
        ]:
            raise BusinessRuleViolation("Anda tidak memilik hak untuk melakukan ini")

        # cek udah dipecat apa belom
        if actor_membership.left_at is not None:
            raise BusinessRuleViolation("Membership actor sudah tidak aktif")

        if target_membership.left_at is not None:
            raise BusinessRuleViolation("Membership target sudah tidak aktif")

        # cek bisnis rule
        is_delete_self = actor_membership.user_id == target_membership.user_id

        # cek OWNER
        if actor_membership.role == TenantMembership.Role.OWNER:
            # OWNER gak bisa apus dirinya sendiri
            if is_delete_self:
                raise BusinessRuleViolation("Owner tidak bisa hapus diri anda sendiri")
            # Owner gak bisa apus OWNER LAIN
            if target_membership.role == TenantMembership.Role.OWNER:
                raise BusinessRuleViolation("Owner tidak bisa menghapus owner lain")

        # cek Manager
        elif actor_membership.role == TenantMembership.Role.MANAGER:
            # MANAGER gak bisa apus dirinya sendiri
            if is_delete_self:
                raise BusinessRuleViolation("Manager, tidak bisa hapus diri sendiri")
            # kalo mau apus owner
            if target_membership.role == TenantMembership.Role.OWNER:
                raise BusinessRuleViolation("Manager, tidak bisa menghapus Owner")
            # kalo mau apus sesama manager
            if target_membership.role == TenantMembership.Role.MANAGER:
                raise BusinessRuleViolation(
                    "Manager, tidak bisa menghapus sesama Manager"
                )

        # apply perubahan (soft delete)
        target_membership.left_at = timezone.now()
        target_membership.save(update_fields=["left_at"])

        # response
        return None


# mastiin user adalah member aktif dari tenant
def get_current_active_membership(*, user: User, tenant_id: int) -> TenantMembership:

    try:
        return TenantMembership.objects.get(
            tenant_id=tenant_id,
            user=user,
            left_at__isnull=True,
        )
    except TenantMembership.DoesNotExist:
        raise ResourceNotFound("Membership not Found!")


def update_tenant_timezone_service(
    *, actor_membership: TenantMembership, data: UpdateTimezoneDTO
) -> Tenant:
    # authorization
    if actor_membership.role != TenantMembership.Role.OWNER:
        raise BusinessRuleViolation("Anda tidak memiliki hak untuk melakukan ini!")

    tenant = actor_membership.tenant
    tenant.timezone = data.timezone

    tenant.save(update_fields=["timezone"])

    return tenant
