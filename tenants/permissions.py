from rest_framework.permissions import BasePermission
from .models import TenantMembership
from core.thread_local import get_current_tenant

class IsTenantManager(BasePermission):
    """
        BUAT MASTTIN ROLE USER YANG MASUK ADALAH MANAGER
    """
    def has_permission(self, request, view): 
        # ambil requestnya dan cek apakah dia udah login 
        if not request.user.is_authenticated:
            return False       
        
        # cek ke database
        is_manager = TenantMembership.objects.filter(
            user=request.user, role=TenantMembership.Role.MANAGER
            ).exists()
                
        return is_manager