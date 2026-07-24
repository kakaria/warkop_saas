import pytest

from tenants.models import Tenant, TenantMembership
from tenants.services import public_onboarding_orchestrator
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

