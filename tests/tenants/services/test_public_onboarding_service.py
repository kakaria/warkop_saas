import pytest

from core.exceptions import BusinessRuleViolation
from tenants.models import Tenant, TenantMembership
from tenants.services import (
    public_onboarding_orchestrator,
)
from users.models import User


@pytest.mark.django_db
def test_public_onboarding_success(
    valid_onboarding_payload,
):
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0

    new_user = public_onboarding_orchestrator(
        email=valid_onboarding_payload["email"],
        password=valid_onboarding_payload["password"],
        full_name=valid_onboarding_payload["full_name"],
        tenant_name=valid_onboarding_payload["tenant_name"],
        tenant_address=valid_onboarding_payload["tenant_address"],
    )
    assert User.objects.filter(email=new_user.email).count() == 1
    assert (
        Tenant.objects.filter(name=valid_onboarding_payload["tenant_name"]).count() == 1
    )
    assert TenantMembership.objects_global.filter(user=new_user.id).count() == 1


@pytest.mark.django_db
def test_public_onboarding_rollback_when_assign_user_to_tenant_failed(
    valid_onboarding_payload, monkeypatch
):

    # buktiin db kosong
    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0

    def failed_create(*args, **kwargs):
        raise BusinessRuleViolation("Gagal membuat membership")

    monkeypatch.setattr(
        Tenant.objects,
        "create",
        failed_create,
    )

    with pytest.raises(BusinessRuleViolation):
        public_onboarding_orchestrator(
            email=valid_onboarding_payload["email"],
            password=valid_onboarding_payload["password"],
            full_name=valid_onboarding_payload["full_name"],
            tenant_name=valid_onboarding_payload["tenant_name"],
            tenant_address=valid_onboarding_payload["tenant_address"],
        )

    assert User.objects.count() == 0
    assert Tenant.objects.count() == 0
    assert TenantMembership.objects_global.count() == 0


@pytest.mark.django_db
def test_public_onboarding_rollback_when_assign_user_to_membership_failed(
    valid_onboarding_payload, monkeypatch
):

    def failed_create_membership(*args, **kwargs):
        raise BusinessRuleViolation("Gagal membuat membership!")

    monkeypatch.setattr(
        TenantMembership.objects_global,
        "create",
        failed_create_membership,
    )

    # ACT
    with pytest.raises(BusinessRuleViolation):
        public_onboarding_orchestrator(
            email=valid_onboarding_payload["email"],
            password=valid_onboarding_payload["password"],
            full_name=valid_onboarding_payload["full_name"],
            tenant_name=valid_onboarding_payload["tenant_name"],
            tenant_address=valid_onboarding_payload["tenant_address"],
        )

    assert not User.objects.filter(email=valid_onboarding_payload["email"]).exists()
    assert not TenantMembership.objects_global.filter(
        user__email=valid_onboarding_payload["email"],
        user__full_name=valid_onboarding_payload["full_name"],
    ).exists()
