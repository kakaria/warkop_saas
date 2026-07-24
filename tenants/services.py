import logging

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.exceptions import BussinessRuleViolation
from tenants.models import Tenant, TenantMembership
from users.models import User
from users.services import create_user_account_service

logger = logging.getLogger(__name__)


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


@transaction.atomic
def public_onboarding_orchestrator(
    email: str, password: str, full_name: str, tenant_name: str, tenant_address: str
) -> User:
    """
    buat NYATUIN USER, TENANT, dan TENANTMEMBERSHIP
    """

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


@transaction.atomic
def staff_provising_orchestrator(
    actor_membership: TenantMembership,
    email: str,
    password: str,
    full_name: str,
    role: str,
    current_tenant_id: int,
) -> User:
    """
    for assign new member to tenant
    """

    if not current_tenant_id:
        raise ValueError("Tenant tidak ditemukan di context!")

    # selain owner & manager, tendang
    if actor_membership.role not in [
        TenantMembership.Role.OWNER,
        TenantMembership.Role.MANAGER,
    ]:
        raise PermissionDenied("Maaf, kamu tidak bisa membuat member baru")

    # kalo actor_membership is Manager (cuma bisa bikin kasir)
    if actor_membership.role == TenantMembership.Role.MANAGER:
        if role != TenantMembership.Role.CASHIER:
            raise PermissionDenied("Maaf, Manager hanya bisa membuat member Kasir")

    # ambil object Tenant
    tenant_obj = Tenant.objects.get(id=current_tenant_id)

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


# service untuk ngambil data staff
def get_membership_service(
    tenant_id: int, role: str | None
) -> QuerySet[TenantMembership]:

    # bikin querynya
    queryset = (
        TenantMembership.objects.filter(tenant_id=tenant_id)
        .select_related("user", "tenant")
        .order_by("user")
    )

    # kalo role diisi (cari berdasarkan role)
    if role:
        queryset = queryset.filter(role=role)

    return queryset


@transaction.atomic
def patch_staff_service(
    actor: User, target_membership: TenantMembership, validated_data: dict
) -> TenantMembership:

    # ambil key dari dict validated_data
    new_role = validated_data.get("role")

    # cek apakah apakah role yang dikirim or rolenya sama kayak target saat ini
    if not new_role:
        print("gak ada")
        logger.info(
            "Patch staff aborted: empty payload",
            extra={
                "event": "staff_patch_empty",
                "actor_id": actor.id,
                "target_id": target_membership.id,
            },
        )
        return target_membership
    if target_membership.role == new_role:
        return target_membership

    # ambil membership dari si user filter dengan tenant_id yang sama kayak targetmembership
    try:
        actor_membership = TenantMembership.objects.get(
            tenant=target_membership.tenant, user=actor
        )
    except TenantMembership.DoesNotExist:
        raise PermissionDenied("Anda bukan member di tenant ini")

    # bisnis rule
    # CEK KASIR GAK BOLEH GANTI (HARUSNYA UDAH SI DI PERMISSIONS.PY)
    if actor_membership.role not in [
        TenantMembership.Role.OWNER,
        TenantMembership.Role.MANAGER,
    ]:
        raise PermissionDenied(
            f"Mohon maaf, {actor_membership.role} anda tidak memiliki hak untuk melakukan itu🙇"
        )

    # buat variable, biar gak ngetik
    is_self_edit = actor_membership.id == target_membership.id

    # CEK untuk Manager
    if actor_membership.role == TenantMembership.Role.MANAGER:
        # inget! manager cuma bisa edit staff Kasir, jadi selain kasir tolak aja
        if not is_self_edit and target_membership.role != TenantMembership.Role.CASHIER:
            raise PermissionDenied("Anda manager, hanya bisa edit staff kasir")
        # biar manager gak bisa edit dirinya sendiri (role)
        if is_self_edit and new_role != target_membership.role:
            raise PermissionDenied("Anda gak bisa edit role anda")
        if not is_self_edit and new_role != TenantMembership.Role.CASHIER:
            raise PermissionDenied("Anda cuma bisa angkat user jadi kasir")

    # CEK untuk OWNER
    if actor_membership.role == TenantMembership.Role.OWNER:
        # cek kalo owner mau ngedit dirinya sendiri
        if is_self_edit and new_role in [
            TenantMembership.Role.MANAGER,
            TenantMembership.Role.CASHIER,
        ]:
            raise PermissionDenied("Anda tidak boleh menurunkan jabatan anda sendiri")

    # apply perubahan
    for key, value in validated_data.items():
        setattr(target_membership, key, value)

    # simpen ke database, pake update_fields
    target_membership.save(update_fields=list(validated_data.keys()))

    return target_membership


def remove_member_from_tenant_service(
    actor_membership_id: int, target_membership_id: int
) -> None:  # karena delete gak ngembaliin apapun

    with transaction.atomic():

        print(actor_membership_id)
        print(target_membership_id)

        # ambil actor_membership (pake get() karena kita ngambil berdasarkan id membership)
        try:
            actor_membership = TenantMembership.objects.select_related(
                "user", "tenant"
            ).get(id=actor_membership_id)

        except TenantMembership.DoesNotExist:
            raise BussinessRuleViolation("Maaf member ini tidak ditemukan")

        # ambil target_membership
        try:
            target_membership = TenantMembership.objects.select_for_update().get(
                id=target_membership_id
            )

        except TenantMembership.DoesNotExist:
            raise BussinessRuleViolation("Maaf member ini tidak ditemukan")

        # cek apakah dia selain owner dan manager
        if actor_membership.role not in [
            TenantMembership.Role.OWNER,
            TenantMembership.Role.MANAGER,
        ]:
            raise PermissionDenied(
                "Maaf anda tidak punya hak untuk memecat member lain"
            )

        # cek udah dipecat apa belom
        if actor_membership.left_at is not None:
            raise PermissionDenied("Maaf kamu sudah dipecat")

        if target_membership.left_at is not None:
            raise PermissionDenied("Maaf kamu sudah dipecat")

        # cek apakah aktor dan target satu tenant
        if target_membership.tenant_id != actor_membership.tenant_id:
            raise PermissionDenied("Maaf ternyata kalian beda tenant")

        # cek bisnis rule
        is_delete_self = actor_membership.user_id == target_membership.user_id

        # cek OWNER
        if actor_membership.role == TenantMembership.Role.OWNER:
            # OWNER gak bisa apus dirinya sendiri
            if is_delete_self:
                raise PermissionDenied(
                    "Sebagai Owner, tidak bisa hapus diri anda sendiri"
                )
            # Owner gak bisa apus OWNER LAIN
            if target_membership.role == TenantMembership.Role.OWNER:
                raise PermissionDenied(
                    "Sebagai Owner, anda tidak bisa menghapus owner lain"
                )

        # cek Manager
        if actor_membership.role == TenantMembership.Role.MANAGER:
            # MANAGER gak bisa apus dirinya sendiri
            if is_delete_self:
                raise PermissionDenied(
                    "Anda sebagai Manager, tidak bisa hapus diri anda sendiri"
                )
            # kalo mau apus owner
            if target_membership.role == TenantMembership.Role.OWNER:
                raise PermissionDenied(
                    "Anda sebagai Manager, tidak bisa menghapus Owner"
                )
            # kalo mau apus sesama manager
            if target_membership.role == TenantMembership.Role.MANAGER:
                raise PermissionDenied(
                    "Anda sebagai Manager, tidak bisa menghapus sesama Manager"
                )

        # apply perubahan (soft delete)
        target_membership.left_at = timezone.now()
        target_membership.save(update_fields=["left_at"])

        # response
        return None


# service kecil untuk ambil object membership yang aktif
def current_active_membership(user: User, tenant_id: int):
    return TenantMembership.objects.get(tenant_id=tenant_id, user=user)
