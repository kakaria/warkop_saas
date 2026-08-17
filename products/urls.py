from django.urls import path

from products.views import (
    ProductBasicPatchView,
    ProductCreateAPIView,
    ProductListAPIView,
    ProductRetrieveAPIView,
    StockAdjustmentAPIView,
)

urlpatterns = [
    path("create/", ProductCreateAPIView.as_view(), name="create-product"),
    path("", ProductListAPIView.as_view(), name="products-list"),
    path("<int:pk>/", ProductRetrieveAPIView.as_view(), name="product-detail"),
    path("patch/<int:pk>/", ProductBasicPatchView.as_view(), name="product-patch"),
    path(
        "<int:product_id>/stock-adjustment/",
        StockAdjustmentAPIView.as_view(),
        name="stock_adjustment",
    ),
]
