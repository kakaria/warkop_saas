from django.db import models
from core.managers import ProductTenantManager

class Product(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    stock = models.IntegerField()
    
    # PANGGIL SI SATPAM (Default dengan logika OR)
    objects = ProductTenantManager()
    
    # PANGGIL MANAGER PINTU BELAKANG (Bypass)
    global_objects = models.Manager()
    
    
    
    
    