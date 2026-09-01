import pytest

from core.exceptions import BusinessRuleViolation, ProductNotFoundError
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
    owner_membership_a, tenant_context, productD
):
    tenant_context(owner_membership_a.tenant_id)

    with pytest.raises(ProductNotFoundError):
        archive_product_service(
            actor_membership=owner_membership_a, product_id=productD.id
        )

    productD.refresh_from_db()
    assert not productD.is_archived


@pytest.mark.django_db
def test_archived_product_failed_when_product_is_already_archived(
    cashier_membership, tenant_context, productArchivedC
):
    tenant_context(cashier_membership.tenant_id)

    with pytest.raises(BusinessRuleViolation):
        archive_product_service(
            actor_membership=cashier_membership, product_id=productArchivedC.id
        )
    productArchivedC.refresh_from_db()

    assert productArchivedC.is_archived
