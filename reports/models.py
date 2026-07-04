from django.db import models
from core.managers import StrictTenantManager

from django.utils.translation import gettext_lazy as _
    
class Report(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name='reports')
    
    
    class Status(models.TextChoices):
        PENDING = "PND", _("Pending"),
        GENERATING = "GNR", _("Generating"),
        SUCCESS = "SCS", _("Success"),
        FAILED = "FAI", _("Failed")
        
    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.PENDING
    )
    file_url = models.URLField(null=True, blank=True)
    
    # manager satpam
    objects = StrictTenantManager()
    objects_global = models.Manager()
    
    