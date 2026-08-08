from django.urls import path

from products.views import (
    ProductCreateAPIView,
    ProductListAPIView,
    ProductRetrieveAPIView,
)

urlpatterns = [
    path("create/", ProductCreateAPIView.as_view(), name="create-product"),
    path("list/", ProductListAPIView.as_view(), name="products-list"),
    path("<int:pk>/", ProductRetrieveAPIView.as_view(), name="product-detail"),
]
