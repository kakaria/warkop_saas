from rest_framework.routers import DefaultRouter, SimpleRouter
from django.conf import settings
from .views import OrderViewSet


if settings.DEBUG:
    router = DefaultRouter()
else: # kalo DEBUG = False, gak bisa liat root api
    router = SimpleRouter()

router.register(r"", OrderViewSet)

urlpatterns = router.urls
