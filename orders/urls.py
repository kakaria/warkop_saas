from django.urls import path
from .views import OrderListView

urlpatterns = [
    path('api/orders/', OrderListView.as_view(), name='order-list'),
]