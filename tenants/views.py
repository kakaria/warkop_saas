from rest_framework import viewsets, mixins
from django.contrib.auth import get_user_model
from .serializers import TenantUserSerializer
from .permissions import IsTenantManager
from core.thread_local import get_current_tenant
import logging


logger = logging.getLogger(__name__)
# ambil real Model User
User = get_user_model()

# tujuan view ini, Manager bisa input user baru, GET sesuai tenant_id manager
class TenantUserViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    # ambil serializer
    serializer_class = TenantUserSerializer
    
    # pasang izin yang bisa liat User
    permission_classes = [IsTenantManager] # bentukny harus list
    
    def get_queryset(self):
        
        # ambil tenant_id dari RAM (thread_local)
        tenant_id = get_current_tenant()
        
        # bikin failsafe (kalo gak nemu tenant_id, balikin jadi None)
        if tenant_id is None:
            # kasih jejak digital ke yang lagi nyoba masuk
            logger.warning("FAILSAFE TRIGGERED: tenant_id is None in TenantUserViewSet")
            return User.objects.none()
        
        # balikin, user object yang tenant_idnya sama kayak tenant_id thread_local
        return User.objects.filter(tenant_memberships__tenant_id=tenant_id)
        