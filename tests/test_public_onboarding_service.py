from unittest.mock import patch

import pytest

from tenants.models import Tenant, TenantMembership
from tenants.services import public_onboarding_orchestrator
from users.models import User


@pytest.mark.django_db
def test_public_onboarding_service_mock(valid_onboarding_payload):
    # buktiin db kosong
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0

    print(User.objects.count())

    print(Tenant.objects.count())

    print(TenantMembership.objects_global.count())

    with patch(
        "tenants.services.assign_user_to_tenant_service",
        side_effect=Exception("Boom!"),
    ):
        with pytest.raises(Exception, match="Boom!"):
            public_onboarding_orchestrator(**valid_onboarding_payload)

    print(User.objects.count())

    print(Tenant.objects.count())

    print(TenantMembership.objects_global.count())

    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0
