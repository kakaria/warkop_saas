import pytest

from core.exceptions import BusinessRuleViolation
from tenants.dto import UpdateTimezoneDTO
from tenants.services import update_tenant_timezone_service


@pytest.mark.django_db
def test_update_timezone_failed_when_actor_is_different_tenant(owner_membership_a, tenant_context, tenantA, tenantB):

    # Arrange
    tenant_context(tenantA.id)

    initial_timezone_tenant_b = tenantB.timezone

    data = UpdateTimezoneDTO(timezone="Asia/Makassar")

    # Act

    update_tenant_timezone_service(
        actor_membership=owner_membership_a,
        data=data,
    )

    tenantA.refresh_from_db()
    tenantB.refresh_from_db()

    assert tenantA.timezone == "Asia/Makassar"
    assert tenantB.timezone == initial_timezone_tenant_b


@pytest.mark.django_db
def test_update_timezone_failed_when_user_is_cashier(
    cashier_membership, tenant_context, tenantA
):
    # Arrange
    tenant_context(tenantA.id)

    initial_timezone = tenantA.timezone

    data = UpdateTimezoneDTO(timezone="Asia/Makassar")

    # Act
    with pytest.raises(BusinessRuleViolation) as exc:
        update_tenant_timezone_service(
            actor_membership=cashier_membership,
            data=data,
        )

    tenantA.refresh_from_db()

    assert tenantA.timezone == initial_timezone


@pytest.mark.django_db
def test_update_timezone_success(owner_membership_a, tenant_context, tenantA):
    # Arrange
    tenant_context(tenantA.id)

    data = UpdateTimezoneDTO(timezone="Asia/Makassar")

    # Act
    update_tenant_timezone_service(
        actor_membership=owner_membership_a,
        data=data,
    )

    tenantA.refresh_from_db()

    assert tenantA.timezone == "Asia/Makassar"
