from rest_framework.routers import DefaultRouter

from .views import TenantUserViewSet

# gunain Routers (karena gua make ViewSet)
router = DefaultRouter()

router.register(r"users", TenantUserViewSet, basename="tenant-user")

urlpatterns = router.urls
