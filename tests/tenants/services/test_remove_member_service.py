import pytest
from django.core.exceptions import PermissionDenied

from core.exceptions import BusinessRuleViolation
from tenants.services import remove_member_from_tenant_service


@pytest.mark.django_db
def test_owner_can_remove_cashier(
    owner_membership_a, cashier_membership, tenant_context
):

    # ==== ARRANGE
    tenant_context(owner_membership_a.tenant_id)

    # ==== ACT
    # panggil service
    remove_member_from_tenant_service(
        actor_membership=owner_membership_a,
        target_membership_id=cashier_membership.id,
    )

    # ==== ASSERT
    # refresh db (buat manggil lagi object si cashier_membership setelah kita update_field['left_at'])
    cashier_membership.refresh_from_db()

    # cek apakah cashier is not None
    assert cashier_membership.left_at is not None


@pytest.mark.django_db
def test_manager_can_remove_cashier(
    manager_membership, cashier_membership, tenant_context
):

    # ===== ARRANGE
    # setting local_thread
    tenant_context(manager_membership.tenant_id)

    # ===== ACT
    remove_member_from_tenant_service(
        actor_membership=manager_membership,
        target_membership_id=cashier_membership.id,
    )

    # ==== ASSERT
    # refresh database
    print("udah disini")
    cashier_membership.refresh_from_db()
    assert cashier_membership.left_at is not None


@pytest.mark.django_db
def test_manager_cannot_remove_owner(
    manager_membership, owner_membership_a, tenant_context
):

    tenant_context(manager_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        remove_member_from_tenant_service(
            actor_membership=manager_membership,
            target_membership_id=owner_membership_a.id,
        )

    owner_membership_a.refresh_from_db()

    assert owner_membership_a.left_at is None


@pytest.mark.django_db
def test_cashier_cannot_remove_member(
    cashier_membership, owner_membership_a, manager_membership, tenant_context
):

    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        remove_member_from_tenant_service(
            actor_membership=cashier_membership,
            target_membership_id=owner_membership_a.id,
        )

    owner_membership_a.refresh_from_db()

    assert owner_membership_a.left_at is None


@pytest.mark.django_db
def test_cannot_remove_member_from_other_tenant(
    owner_membership_b, manager_membership, tenant_context
):

    # isi tenant owner
    tenant_context(owner_membership_b.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        remove_member_from_tenant_service(
            actor_membership=owner_membership_b,
            target_membership_id=manager_membership.id,
        )

    manager_membership.refresh_from_db()

    assert manager_membership.left_at is None
