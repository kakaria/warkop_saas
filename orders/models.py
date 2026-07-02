from django.db import models
from decimal import Decimal

class Order(models.Model):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.0))


class DetailOrder(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT, related_name='order_detail')
    quantity = models.IntegerField()
    price_at_transaction = models.DecimalField(max_digits=10, decimal_places=2)
    
    
    
    