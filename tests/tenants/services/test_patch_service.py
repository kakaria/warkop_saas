import pytest

from core.exceptions import BusinessRuleViolation
from tenants.models import TenantMembership
from tenants.services import patch_staff_service


@pytest.mark.django_db
def test_owner_change_role_staff_success(
    owner_membership_a, tenant_context, manager_membership
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    validated_data = {
        "role": TenantMembership.Role.CASHIER,
    }

    # Act
    result = patch_staff_service(
        actor_membership=owner_membership_a,
        target_membership=manager_membership,
        validated_data=validated_data,
    )

    result.refresh_from_db()

    assert result.role == validated_data["role"]


@pytest.mark.django_db
def test_owner_patch_same_role_is_noop(
    owner_membership_a,
    tenant_context,
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    validated_data = {
        "role": TenantMembership.Role.OWNER,
    }

    # Act
    result = patch_staff_service(
        actor_membership=owner_membership_a,
        target_membership=owner_membership_a,
        validated_data=validated_data,
    )

    result.refresh_from_db()

    assert result.role == validated_data["role"]


@pytest.mark.django_db
def test_owner_cannot_demote_own_role(
    owner_membership_a,
    tenant_context,
):
    # Arrange
    tenant_context(owner_membership_a.tenant_id)

    target = owner_membership_a
    original_role = target.role

    validated_data = {
        "role": TenantMembership.Role.CASHIER,
    }

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        patch_staff_service(
            actor_membership=owner_membership_a,
            target_membership=owner_membership_a,
            validated_data=validated_data,
        )

    target.refresh_from_db()

    assert "tidak boleh menurunkan jabatan anda sendiri" in str(exc.value).lower()
    assert target.role == original_role


@pytest.mark.django_db
def test_manager_cannot_patch_role(
    manager_membership,
    cashier_membership,
    tenant_context,
):
    # Arrange
    tenant_context(manager_membership.tenant_id)

    target = cashier_membership
    original_role = target.role

    validated_data = {
        "role": TenantMembership.Role.MANAGER,
    }

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        patch_staff_service(
            actor_membership=manager_membership,
            target_membership=cashier_membership,
            validated_data=validated_data,
        )

    target.refresh_from_db()

    assert "tidak memiliki hak" in str(exc.value).lower()
    assert target.role == original_role


@pytest.mark.django_db
def test_cashier_cannot_patch_role(
    cashier_membership,
    manager_membership,
    tenant_context,
):
    # Arrange
    tenant_context(cashier_membership.tenant_id)

    target = manager_membership
    original_role = target.role

    validated_data = {
        "role": TenantMembership.Role.CASHIER,
    }

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        patch_staff_service(
            actor_membership=cashier_membership,
            target_membership=manager_membership,
            validated_data=validated_data,
        )

    target.refresh_from_db()

    assert "tidak memiliki hak" in str(exc.value).lower()
    assert target.role == original_role


@pytest.mark.django_db
def test_patch_staff_service_respect_tenant_scope(
    owner_membership_b,
    manager_membership,
    tenant_context,
):
    # Arrange
    tenant_context(owner_membership_b.tenant_id)

    target = manager_membership
    original_role = target.role

    validated_data = {
        "role": TenantMembership.Role.CASHIER,
    }

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        patch_staff_service(
            actor_membership=owner_membership_b,
            target_membership=manager_membership,
            validated_data=validated_data,
        )

    target.refresh_from_db()

    assert "tidak memiliki hak" in str(exc.value).lower()
    assert target.role == original_role


@pytest.mark.django_db
def test_owner_inactive_cannot_patch_staff(
    owner_membership_a_inactive,
    manager_membership,
    tenant_context,
):
    # Arrange
    tenant_context(owner_membership_a_inactive.tenant_id)

    target = manager_membership
    original_role = target.role

    validated_data = {
        "role": TenantMembership.Role.CASHIER,
    }

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        patch_staff_service(
            actor_membership=owner_membership_a_inactive,
            target_membership=manager_membership,
            validated_data=validated_data,
        )

    target.refresh_from_db()

    assert "bukan member aktif" in str(exc.value).lower()
    assert target.role == original_role
