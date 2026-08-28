from datetime import datetime

from django.db.models.aggregates import Max, Sum
from django.utils import timezone

from core.exceptions import BusinessRuleViolation
from orders.models import Order, OrderItem
from products.models import Product, StockMovement
from tenants.models import TenantMembership
from tenants.time import get_business_date, get_business_day_boundary


def get_today_order_count_service(
    *,
    actor_membership: TenantMembership,
    now: datetime | None = None,
) -> int:
    tenant = actor_membership.tenant

    if now is None:
        now = timezone.now()

    business_date = get_business_date(
        timezone_name=tenant.timezone,
        now=now,
    )

    start_utc, end_utc = get_business_day_boundary(
        timezone_name=tenant.timezone,
        business_date=business_date,
    )

    return Order.objects.filter(
        tenant_id=actor_membership.tenant_id,
        created_at__gte=start_utc,
        created_at__lt=end_utc,
    ).count()


def get_today_product_sales_service(
    *,
    actor_membership: TenantMembership,
    now: datetime | None = None,
) -> list[dict]:

    if now is None:
        now = timezone.now()

    tenant = actor_membership.tenant
    business_date = get_business_date(timezone_name=tenant.timezone, now=now)
    start_utc, end_utc = get_business_day_boundary(
        timezone_name=tenant.timezone, business_date=business_date
    )

    # group by pada id
    historical_sales = (
        OrderItem.objects.filter(
            order__tenant_id=actor_membership.tenant_id,
            order__status__in=[
                Order.Status.PENDING,
                Order.Status.PAID,
            ],
            order__created_at__gte=start_utc,
            order__created_at__lt=end_utc,
        )
        .values("product_id")
        .annotate(
            quantity_sold=Sum("quantity"),
            gross_order_value=Sum("sub_total"),
            historical_name=Max("product_name_at_transaction"),
        )
    )

    # bikin dict pencarian O(1)
    sales_map = {
        item["product_id"]: {
            "qty": item["quantity_sold"],
            "gross_order_value": item["gross_order_value"],
            "historical_name": item["historical_name"],
        }
        for item in historical_sales
    }

    # ambil product active (katalog)
    active_products = Product.objects.filter(
        tenant_id=actor_membership.tenant_id,
        is_archived=False,
    ).values("id", "name")

    active_products_map = {item["id"]: item["name"] for item in active_products}
    all_relevant_ids = set(active_products_map.keys()).union(set(sales_map.keys()))

    # merger data product yang terjual,sama yang gak terjual (masih di katalog tapi belom terjual)
    final_report = []
    for product_id in all_relevant_ids:
        sales_data = sales_map.get(product_id)

        # penentuan nama product
        if product_id in active_products_map:
            # kalo masih aktif, pake nama dari catalog
            final_name = active_products_map[product_id]
        else:
            # kalo udah di arsip, pake nama historical name
            final_name = sales_data["historical_name"]

        final_report.append(
            {
                "product_id": product_id,
                "product_name": final_name,
                "quantity_sold": sales_data["qty"] if sales_data else 0,
                "gross_order_value": (
                    sales_data["gross_order_value"] if sales_data else 0
                ),
            }
        )

    final_report.sort(key=lambda x: (-x["quantity_sold"], x["product_id"]))

    return final_report


def get_today_stock_movement_service(
    actor_membership: TenantMembership,
    now: datetime | None = None,
) -> list[dict]:

    # authorization
    if actor_membership.role not in [
        TenantMembership.Role.OWNER,
        TenantMembership.Role.MANAGER,
    ]:
        raise BusinessRuleViolation("Anda tidak memiliki hak untuk melakukan ini!")

    if now is None:
        now = timezone.now()

    tenant = actor_membership.tenant

    business_date = get_business_date(
        timezone_name=tenant.timezone,
        now=now,
    )

    start_utc, end_utc = get_business_day_boundary(
        timezone_name=tenant.timezone,
        business_date=business_date,
    )

    return list(
        StockMovement.objects.filter(
            product__tenant_id=actor_membership.tenant_id,
            created_at__gte=start_utc,
            created_at__lt=end_utc,
        )
        .values(
            "id",
            "product_id",
            "action",
            "quantity",
            "reason",
            "notes",
            "created_by",
            "created_at",
        )
        .order_by("created_at", "id")
    )
