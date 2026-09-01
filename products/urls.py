from django.urls import path

from products.views import (
    ArchiveProductAPIView,
    ProductBasicPatchView,
    ProductCreateAPIView,
    ProductListAPIView,
    ProductRetrieveAPIView,
    StockAdjustmentAPIView,
    StockMovementByProductListAPIView,
    StockMovementDetailAPIView,
    UnarchiveProductAPIView,
)

urlpatterns = [
    path("create/", ProductCreateAPIView.as_view(), name="create-product"),
    path("", ProductListAPIView.as_view(), name="products-list"),
    path("<int:pk>/", ProductRetrieveAPIView.as_view(), name="product-detail"),
    path("patch/<int:pk>/", ProductBasicPatchView.as_view(), name="product-patch"),
    path(
        "<int:product_id>/archive/",
        ArchiveProductAPIView.as_view(),
        name="product-archive",
    ),
    path(
        "<int:product_id>/restore/",
        UnarchiveProductAPIView.as_view(),
        name="product-restore",
    ),
    path(
        "stock-movement/",
        StockMovementByProductListAPIView.as_view(),
        name="list-stock_movement",
    ),
    path(
        "<int:product_id>/stock-movement/",
        StockMovementDetailAPIView.as_view(),
        name="list-stock_movement",
    ),
    path(
        "<int:product_id>/stock-adjustment/",
        StockAdjustmentAPIView.as_view(),
        name="stock_adjustment",
    ),
]
