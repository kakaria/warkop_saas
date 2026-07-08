from sre_constants import SUCCESS
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


from core.managers import StrictTenantManager
from core.thread_local import set_current_tenant


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class TenantMembership(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='tenant_membership' )
    
    class Role(models.TextChoices):
        OWNER = "OWN", _("Owner"),
        MANAGER = "MNG", _("Manager"),
        CASHIER = "CSH", _("Cashier")
    
    role = models.CharField(
        max_length=3, 
        choices = Role.choices
    )
    
    objects = StrictTenantManager()
    objects_global = models.Manager()
    

