import pytest
from django.core.management import call_command

from orders.models import Order
from products.models import Product
from tenants.models import Tenant
from users.models import User


def _counts():
    return (
        Tenant.objects.count(),
        User.objects.count(),
        Product.global_objects.count(),
        Order.global_objects.count(),
    )


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    first = _counts()

    call_command("seed_demo")

    assert _counts() == first
    assert Tenant.objects.count() == 2
    assert Order.global_objects.filter(status=Order.Status.VOID).count() == 1
