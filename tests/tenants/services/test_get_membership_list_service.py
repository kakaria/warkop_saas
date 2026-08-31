import pytest

from core.exceptions import BusinessRuleViolation
from tenants.models import TenantMembership
from tenants.services import assign_user_to_tenant_service, get_membership_list_service
from users.models import User


@pytest.mark.django_db
def test_get_membership_list_success(owner_membership_a, tenant_context, tenantA):
    # Arrange

    assert TenantMembership.objects.count() == 0

    tenant_context(tenantA.id)

    # bikin user
    def create_user_and_assign_to_tenant(email, password, full_name, role):
        user = User.objects.create(
            email=email,
            password=password,
            full_name=full_name,
        )
        # assign user to tenant service
        membership = assign_user_to_tenant_service(user=user, tenant=tenantA, role=role)

        return membership

    create_user_and_assign_to_tenant("udin@gmail.com", "ud1N)_1`", "udin nich", "MNG")
    create_user_and_assign_to_tenant("dono@gmail.com", "ud1N)_1`", "dono nich", "CSH")

    # Act
    membership_list = get_membership_list_service(
        actor_membership=owner_membership_a,
    )

    assert membership_list.count() == 3
    assert TenantMembership.objects.filter(tenant_id=tenantA.id).count() == 3


@pytest.mark.django_db
def test_get_membership_list__respect_tenant_scope(
    owner_membership_a, tenant_context, tenantA, tenantB
):
    # Arrange
    assert TenantMembership.objects.count() == 0

    def create_user_and_assign_to_tenant(email, password, full_name, role, tenant):
        user = User.objects.create(
            email=email,
            password=password,
            full_name=full_name,
        )
        # assign user to tenant service
        membership = assign_user_to_tenant_service(user=user, tenant=tenant, role=role)

        return membership

    # bikin user tenant A
    tenant_context(tenantA.id)
    user_a = create_user_and_assign_to_tenant(
        "udin@gmail.com", "ud1N)_1`", "udin nich", "MNG", tenantA
    )

    # bikin user tenant B
    tenant_context(tenantB.id)
    user_b = create_user_and_assign_to_tenant(
        "dono@gmail.com", "ud1N)_1`", "dono nich", "CSH", tenantB
    )

    # Act
    tenant_context(tenantA.id)
    result = get_membership_list_service(
        actor_membership=owner_membership_a,
    )

    assert result.count() == 2

    result_membership_ids = [member.id for member in result]
    assert owner_membership_a.id in result_membership_ids
    assert user_a.id in result_membership_ids
    assert user_b.id not in result_membership_ids


@pytest.mark.django_db
def test_get_membership_list_failed_when_actor_is_cashier(
    cashier_membership, tenant_context, tenantA
):
    # Arrange
    tenant_context(tenantA.id)
    with pytest.raises(BusinessRuleViolation) as exc_info:
        get_membership_list_service(
            actor_membership=cashier_membership,
        )

    assert "tidak memiliki hak" in str(exc_info.value).lower()
