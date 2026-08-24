import pytest

from core.exceptions import BusinessRuleViolation
from products.services import archive_product_service


@pytest.mark.django_db
def test_archived_product_success(owner_membership_a, tenant_context, product):
    tenant_context(owner_membership_a.tenant_id)

    product_archive = archive_product_service(
        actor_membership=owner_membership_a, product_id=product.id
    )

    product_archive.refresh_from_db()

    assert product_archive.is_archived


@pytest.mark.django_db
def test_archived_product_failed_when_actor_is_cashier(
    cashier_membership, tenant_context, product
):
    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        archive_product_service(
            actor_membership=cashier_membership, product_id=product.id
        )

    product.refresh_from_db()

    assert not product.is_archived


@pytest.mark.django_db
def test_archived_product_failed_when_product_in_other_tenant(
    owner_membership_a, tenant_context, productB
):
    tenant_context(owner_membership_a.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        archive_product_service(
            actor_membership=owner_membership_a, product_id=productB.id
        )

    productB.refresh_from_db()
    assert not productB.is_archived


@pytest.mark.django_db
def test_archived_product_failed_when_product_is_already_archived(
    cashier_membership, tenant_context, productC
):
    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        archive_product_service(
            actor_membership=cashier_membership, product_id=productC.id
        )
    productC.refresh_from_db()

    assert productC.is_archived
