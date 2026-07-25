from unittest.mock import patch

import pytest

from tenants.models import Tenant, TenantMembership
from tenants.services import (
    public_onboarding_orchestrator,
    staff_provising_orchestrator,
)
from users.models import User


@pytest.mark.django_db
def test_public_onboarding_rollback_when_assign_user_to_tenant_failed(
    valid_onboarding_payload,
):

    # buktiin db kosong
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0

    with patch(
        "tenants.services.assign_user_to_tenant_service",
        side_effect=Exception("Boom!"),
    ):
        with pytest.raises(Exception, match="Boom!"):
            public_onboarding_orchestrator(**valid_onboarding_payload)

    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0


@pytest.mark.django_db
def test_staff_provising_rollback_when_membership_creation_failed(staff_payload):

    # cara ganti value dari staff_payload
    staff_payload["role"] = TenantMembership.Role.CASHIER
    
    assert not User.objects.filter(email=staff_payload["email"]).exists()
    assert not TenantMembership.objects_global.filter(
        user__email=staff_payload["email"]
    ).exists()

    with patch(
        "tenants.services.assign_user_to_tenant_service",
        side_effect=Exception("Boom!"),
    ):
        with pytest.raises(Exception, match="Boom!"):
            staff_provising_orchestrator(**staff_payload)

    assert not User.objects.filter(email=staff_payload["email"]).exists()
    assert not TenantMembership.objects_global.filter(
        user__email=staff_payload["email"]
    ).exists()
