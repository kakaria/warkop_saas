from rest_framework import generics
from .models import Order
from .serializers import OrderSerializer

class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    
    # KUNCI ARSITEKTUR: Panggil .all() dengan santai. 
    # Sang Satpam (Middleware & TenantManager) yang akan berdarah-darah memfilternya!
    # queryset = Order.objects.all()
    
    def get_queryset(self):
        return Order.objects.all()