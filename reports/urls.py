from django.urls import path

from reports.views import (
    TodayOrderCountAPIView,
    TodayProductSalesAPIView,
    TodayStockMovementAPIView,
)

urlpatterns = [
    path("orders/today/", TodayOrderCountAPIView.as_view(), name="today-order-count"),
    path(
        "products/today/",
        TodayProductSalesAPIView.as_view(),
        name="today-product-sales",
    ),
    path(
        "stock-movements/today/",
        TodayStockMovementAPIView.as_view(),
        name="today-stock-movements",
    ),
]
