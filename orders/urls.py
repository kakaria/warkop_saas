from django.conf import settings
from django.urls import path

from .views import OrderCreateAPIView

urlpatterns = [
    path("", OrderCreateAPIView.as_view(), name="create-orders"),
]
