import pytest

from core.thread_local import clear_thread_local, set_current_tenant
from products.models import Product
from tenants.models import Tenant, TenantMembership
from users.models import User


@pytest.fixture
def tenantA():
    return Tenant.objects.create(
        name="Tenant A",
        address="Jl. Testing no 1",
    )


@pytest.fixture
def tenantB():
    return Tenant.objects.create(
        name="Tenant B",
        address="Jl. Testing no 2",
    )


@pytest.fixture
def owner_user():  # karena pake custom manager, jadinya pake create_user
    return User.objects.create_user(
        email="user1@test.com", password="user-213", full_name="user-user1"
    )


@pytest.fixture
def owner_membership_a(
    tenantA, owner_user
):  # gak perlu pake role bla bla bla, karena testnya jelas test_owner_delete_cashier
    return TenantMembership.objects.create(
        tenant=tenantA,
        user=owner_user,
        role=TenantMembership.Role.OWNER,
        left_at=None,
    )


@pytest.fixture
def owner_membership_b(
    tenantB, owner_user
):  # gak perlu pake role bla bla bla, karena testnya jelas test_owner_delete_cashier
    return TenantMembership.objects.create(
        tenant=tenantB,
        user=owner_user,
        role=TenantMembership.Role.OWNER,
        left_at=None,
    )


@pytest.fixture
def cashier_user():  # karena pake custom manager, jadinya pake create_user
    return User.objects.create_user(
        email="cashier1@test.com", password="cashier-213", full_name="cashier1"
    )


@pytest.fixture
def cashier_membership(tenantA, cashier_user):
    return TenantMembership.objects.create(
        tenant=tenantA,
        user=cashier_user,
        role=TenantMembership.Role.CASHIER,
        left_at=None,
    )


@pytest.fixture
def manager_user():
    return User.objects.create_user(
        email="manager01@test.com",
        password="321manager",
        full_name="manager01",
    )


@pytest.fixture
def manager_membership(tenantA, manager_user):
    return TenantMembership.objects.create(
        tenant=tenantA,
        user=manager_user,
        role=TenantMembership.Role.MANAGER,
        left_at=None,
    )


@pytest.fixture
def tenant_context():
    # fungsi untuk set tenant, karea fixture gak nerima data biasa, dia nerima fungsi fixture
    def _set(tenant_id):
        set_current_tenant(tenant_id)

    yield _set  # berhenti dulu, dan kasih _set ke yang manggil fixture

    clear_thread_local()


@pytest.fixture
def valid_onboarding_payload():
    """
    dict isi data user dan tenant
    """
    return {
        "email": "test01@me.me",
        "password": "don'ttestmebro!",
        "full_name": "how are you?",
        "tenant_name": "good tenant",
        "tenant_address": "st. dont be fraud",
    }


@pytest.fixture
def staff_payload(owner_membership_a):
    return {
        "actor_membership": owner_membership_a,
        "email": "test01@me.me",
        "password": "don'ttestmebro!",
        "full_name": "how are you?",
        "role": TenantMembership.Role.MANAGER,
        "current_tenant_id": owner_membership_a.tenant_id,
    }


@pytest.fixture
def product(tenantA):
    return Product.objects.create(
        tenant=tenantA,
        name="productA",
        price=1000,
        stock=10,
    )


@pytest.fixture
def productB(tenantA):
    return Product.objects.create(
        tenant=tenantA,
        name="ProductB",
        price=15000,
        stock=50,
    )


@pytest.fixture
def productC(tenantA):
    return Product.objects.create(
        tenant=tenantA,
        name="ProductC",
        price=15000,
        stock=50,
    )
