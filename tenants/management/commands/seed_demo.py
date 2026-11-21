"""
Seed demo data. Semua kredensial di sini KHUSUS DEMO, bukan secret.
Jalankan: python manage.py seed_demo   (aman dijalankan berulang)
"""

from contextlib import contextmanager

from django.core.management.base import BaseCommand
from django.db import transaction

from core.thread_local import clear_thread_local, set_current_tenant
from orders.dto import CreateOrderDTO, OrderItemDTO, VoidOrderDTO
from orders.services import (
    create_order_service,
    order_paid_service,
    order_void_service,
)
from products.dto import CreateProductDTO
from products.models import ReasonChoices, StockMovement
from products.services import adjust_stock_service, create_product_service
from tenants.models import TenantMembership
from tenants.services import (
    public_onboarding_orchestrator,
    staff_provising_orchestrator,
)
from users.models import User

Role = TenantMembership.Role
DEMO_PASSWORD = "DemoPass123"

SENJA = {
    "name": "Warkop Senja",
    "address": "Jl. Melati No. 10, Jakarta",
    "owner": ("owner.senja@warkop-demo.test", "Siti Owner"),
    "staff": [
        ("manager", Role.MANAGER, "manager.senja@warkop-demo.test", "Budi Manager"),
        ("cashier", Role.CASHIER, "cashier.senja@warkop-demo.test", "Rina Cashier"),
    ],
}
PAGI = {
    "name": "Kopi Pagi",
    "address": "Jl. Kenanga No. 5, Bandung",
    "owner": ("owner.pagi@warkop-demo.test", "Andi Owner"),
    "staff": [
        ("cashier", Role.CASHIER, "cashier.pagi@warkop-demo.test", "Dewi Cashier"),
    ],
}


@contextmanager
def as_tenant(tenant_id):
    # Manager tenant-aware membaca tenant dari thread-local, jadi di luar
    # request kita set manual lalu bersihkan lagi.
    set_current_tenant(tenant_id)
    try:
        yield
    finally:
        clear_thread_local()


def _membership(user, tenant):
    return TenantMembership.objects_global.get(
        user=user, tenant=tenant, left_at__isnull=True
    )


def _create_tenant(spec):
    owner_email, owner_name = spec["owner"]
    owner = public_onboarding_orchestrator(
        email=owner_email,
        password=DEMO_PASSWORD,
        full_name=owner_name,
        tenant_name=spec["name"],
        tenant_address=spec["address"],
    )
    owner_m = TenantMembership.objects_global.select_related("tenant").get(
        user=owner, role=Role.OWNER
    )
    members = {"owner": owner_m}
    for key, role, email, name in spec["staff"]:
        staff = staff_provising_orchestrator(
            actor_membership=owner_m,
            email=email,
            password=DEMO_PASSWORD,
            full_name=name,
            role=role,
        )
        members[key] = _membership(staff, owner_m.tenant)
    return owner_m.tenant, members


def _products(owner_m, items):
    return {
        name: create_product_service(
            actor_membership=owner_m,
            data=CreateProductDTO(name=name, price=price, stock=stock),
        )
        for name, price, stock in items
    }


def _order(cashier_m, lines):
    items = tuple(OrderItemDTO(product_id=p.id, quantity=q) for p, q in lines)
    return create_order_service(
        actor_membership=cashier_m, data=CreateOrderDTO(items=items)
    )


def _stock(actor_m, product, reason, action, quantity, notes=""):
    return adjust_stock_service(
        actor_membership=actor_m,
        product_id=product.id,
        validated_data={
            "reason": reason,
            "action": action,
            "quantity": quantity,
            "notes": notes,
        },
    )


def _seed_senja(m):
    p = _products(
        m["owner"],
        [
            ("Kopi Susu", 18000, 50),
            ("Es Teh Manis", 8000, 80),
            ("Roti Bakar", 15000, 30),
        ],
    )
    _stock(
        m["owner"],
        p["Kopi Susu"],
        ReasonChoices.RESTOCK,
        StockMovement.Action.ADD,
        20,
        "Restock mingguan",
    )
    _stock(
        m["manager"],
        p["Roti Bakar"],
        ReasonChoices.DAMAGED,
        StockMovement.Action.DEDUCT,
        2,
        "Jatuh saat disajikan",
    )

    paid = _order(m["cashier"], [(p["Kopi Susu"], 2), (p["Roti Bakar"], 1)])
    order_paid_service(actor_membership=m["manager"], order_id=paid.id)

    voided = _order(m["cashier"], [(p["Es Teh Manis"], 3)])
    order_void_service(
        actor_membership=m["manager"],
        order_id=voided.id,
        data=VoidOrderDTO(
            reason=ReasonChoices.ORDER_VOID, notes="Pelanggan membatalkan pesanan"
        ),
    )

    _order(m["cashier"], [(p["Kopi Susu"], 1)])  # dibiarkan PENDING


def _seed_pagi(m):
    p = _products(m["owner"], [("Americano", 20000, 40), ("Croissant", 22000, 25)])
    _order(m["cashier"], [(p["Americano"], 1)])


class Command(BaseCommand):
    help = (
        "Seed demo tenants, users, products, orders, and stock movements (idempotent)."
    )

    def handle(self, *args, **options):
        for spec, seeder in [(SENJA, _seed_senja), (PAGI, _seed_pagi)]:
            if User.objects.filter(email=spec["owner"][0]).exists():
                self.stdout.write(f"skip: {spec['name']} already seeded")
                continue
            with transaction.atomic():
                tenant, members = _create_tenant(spec)
                with as_tenant(tenant.id):
                    seeder(members)
            self.stdout.write(
                self.style.SUCCESS(f"seeded: {spec['name']} (tenant id {tenant.id})")
            )

        self.stdout.write(f"\nDemo password for all accounts: {DEMO_PASSWORD}")
        for spec in (SENJA, PAGI):
            owner_email = spec["owner"][0]
            tenant = (
                TenantMembership.objects_global.select_related("tenant")
                .get(user__email=owner_email, role=Role.OWNER)
                .tenant
            )
            self.stdout.write(f"{spec['name']} -> X-Tenant-Id: {tenant.id}")
            for email in [owner_email] + [s[2] for s in spec["staff"]]:
                self.stdout.write(f"  {email}")
