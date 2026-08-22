from django.urls import path

from products.views import (
    AdminProductListAPIView,
    ArchiveProductAPIView,
    ProductBasicPatchView,
    ProductCreateAPIView,
    ProductListAPIView,
    ProductRetrieveAPIView,
    StockAdjustmentAPIView,
    UnArchiveProductAPIView,
)

urlpatterns = [
    path("create/", ProductCreateAPIView.as_view(), name="create-product"),
    path("", ProductListAPIView.as_view(), name="products-list"),
    path("admin/", AdminProductListAPIView.as_view(), name="admin-products-list"),
    path("<int:pk>/", ProductRetrieveAPIView.as_view(), name="product-detail"),
    path("patch/<int:pk>/", ProductBasicPatchView.as_view(), name="product-patch"),
    path(
        "<int:product_id>/archive/",
        ArchiveProductAPIView.as_view(),
        name="product-archive",
    ),
    path(
        "<int:product_id>/restore/",
        UnArchiveProductAPIView.as_view(),
        name="product-restore",
    ),
    path(
        "<int:product_id>/stock-adjustment/",
        StockAdjustmentAPIView.as_view(),
        name="stock_adjustment",
    ),
]
