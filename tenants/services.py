from re import U

from django.contrib.auth import get_user_model
from django.db import transaction

from core.thread_local import get_current_tenant
from tenants.models import Tenant, TenantMembership
from users.services import create_user_account_service

User = get_user_model()


def create_tenant_service(*, name: str, address: str):
    """
    BIKIN TENANT DOANG
    """
    return Tenant.objects.create(name=name, address=address)


def assign_user_to_tenant_service(user: User, tenant: Tenant, role: str):
    """
    TARO user di tenant tertentu
    """
    return TenantMembership.objects.create(user=user, tenant=tenant, role=role)


@transaction.atomic
def public_onboarding_orchestrator(
    email: str, password: str, tenant_name: str, tenant_address: str
):
    """
    buat NYATUIN USER, TENANT, dan TENANTMEMBERSHIP
    """

    # bikin users
    owner_user = create_user_account_service(email=email, password=password)

    # bikin tenantnya
    tenant_user = create_tenant_service(name=tenant_name, address=tenant_address)

    # sambungin user dan tenant di tenantmembership
    assign_user_to_tenant_service(
        user=owner_user,
        tenant=tenant_user,
        role=TenantMembership.Role.OWNER,  # karena yang bikin user otomatis owner dan dia yang punya tenant
    )

    return owner_user


@transaction.atomic
def staff_provising_orchestrator(email: str, password: str, role: str):
    """
    untuk OWNER NAMBAHIN anak buah ke WARKOP
    bisa MANAGER dan CASHIER
    """

    current_tenant = get_current_tenant()
    if not current_tenant:
        raise ValueError("Tenant tidak ditemukan di context!")

    # bikin usernya dulu
    staff_user = create_user_account_service(email=email, password=password)

    # taro staff_user di tenant yang sesuai
    assign_user_to_tenant_service(user=staff_user, tenant=current_tenant, role=role)

    return staff_user
