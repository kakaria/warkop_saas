from django.conf import settings
from django.urls import path

from .views import (
    OrderCreateAPIView,
    OrderDetailAPIView,
    OrderListAPIView,
    OrderVoidAPIView,
)

urlpatterns = [
    path("create-order/", OrderCreateAPIView.as_view(), name="create-orders"),
    path("", OrderListAPIView.as_view(), name="order-list"),
    path("<int:order_id>/", OrderDetailAPIView.as_view(), name="order-detail"),
    path("<int:order_id>/void-order/", OrderVoidAPIView.as_view(), name="order-void"),
]
