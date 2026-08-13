import pytest
from django.core.exceptions import PermissionDenied

from tenants.models import TenantMembership
from tenants.services import (
    public_onboarding_orchestrator,
    staff_provising_orchestrator,
)
from users.models import User


@pytest.mark.django_db
def test_public_onboarding_creates_owner_membership():

    # Arrange (gak pake fixture karena kita lagi write object baru)
    user = public_onboarding_orchestrator(
        email="owner1@test.com",
        password="owow321",
        full_name="king not here",
        tenant_name="keke shop",
        tenant_address="jl. kudapahit no.32",
    )

    # Act
    membership = TenantMembership.objects_global.get(user=user)

    # Assert
    assert membership.user == user
    assert membership.role == TenantMembership.Role.OWNER
    assert membership.left_at is None
    assert membership.tenant.name == "keke shop"
    assert membership.tenant.address == "jl kudapahit no 32"


@pytest.mark.django_db
def test_provisioning_owner_can_create_manager(owner_membership_b, tenant_context):

    # Arrange
    # tenant_context(owner_membership_b.tenant_id)

    # Act
    new_manager = staff_provising_orchestrator(
        actor_membership=owner_membership_b,
        email="manager01@test.me",
        password="0987654321",
        full_name="my manager 01",
        role=TenantMembership.Role.MANAGER,
        current_tenant_id=owner_membership_b.tenant_id,
    )

    # assert
    assert new_manager.email == "manager01@test.me"

    # karena staff_provising_orchestrator itu return User, ambil TenantMembershipnya
    new_membership = TenantMembership.objects.get(user=new_manager)
    assert new_membership.left_at is None


@pytest.mark.django_db
def test_provisioning_owner_can_create_cashier(owner_membership_a, tenant_context):

    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    # Act
    new_cashier = staff_provising_orchestrator(
        actor_membership=owner_membership_a,
        email="new_cashier1@me.me",
        password="don'tknowthepass321",
        full_name="im the best",
        role=TenantMembership.Role.CASHIER,
        current_tenant_id=owner_membership_a.tenant_id,
    )

    # assert
    assert new_cashier.full_name == "im the best"
    new_membership = TenantMembership.objects.get(user=new_cashier)
    assert new_membership.tenant_id == owner_membership_a.tenant_id


@pytest.mark.django_db
def test_provisioning_manager_can_create_cashier(manager_membership, tenant_context):

    # Arrange
    tenant_context(manager_membership.tenant_id)

    # Act
    new_cashier = staff_provising_orchestrator(
        actor_membership=manager_membership,
        email="new_cashier1@me.me",
        password="don'tknowthepass321",
        full_name="im the best",
        role=TenantMembership.Role.CASHIER,
        current_tenant_id=manager_membership.tenant_id,
    )

    # assert
    assert new_cashier.full_name == "im the best"
    new_membership = TenantMembership.objects.get(user=new_cashier)
    assert new_membership.tenant_id == manager_membership.tenant_id


@pytest.mark.django_db
def test_provisioning_manager_cannot_create_manager(manager_membership, tenant_context):

    tenant_context(manager_membership.tenant_id)

    with pytest.raises(PermissionDenied):
        staff_provising_orchestrator(
            actor_membership=manager_membership,
            email="manager02@me.me",
            password="123",
            full_name="this must no create",
            role=TenantMembership.Role.MANAGER,
            current_tenant_id=manager_membership.tenant_id,
        )

    assert User.objects.filter(email="manager02@me.me").exists()


@pytest.mark.django_db
def test_provisioning_cashier_cannot_create_member(cashier_membership, tenant_context):
    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(PermissionDenied):
        staff_provising_orchestrator(
            actor_membership=cashier_membership,
            email="nottoday@me.me",
            password='don"t you dare',
            full_name="enzo_maresca",
            role=TenantMembership.Role.CASHIER,
            current_tenant_id=cashier_membership.tenant_id,
        )

    assert not User.objects.filter(email="nottoday@me.me").exists()
