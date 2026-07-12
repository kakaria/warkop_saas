from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.thread_local import get_current_tenant
from orders.services import process_checkout, void_order_service

from .models import Order
from .permissions import IsTenantCashier, IsTenantManagerOrOwner
from .serializers import OrderCreateSerializer


class OrderViewSet(
    # mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    # biar muncul pas kita GET
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer

    # def get_permissions(self):  # setting permission
    #     if self.action == "void_order":
    #         return [IsTenantManagerOrOwner()]
    #     return [IsTenantCashier()]

    # def create(self, request, *args, **kwargs):

    #     # panggil serializer CreateOrderSerializer
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)

    #     # ambil tenant
    #     tenant_id = get_current_tenant()

    #     # ambil data bersih (items) terus panggil service layer
    #     order_instance = process_checkout(
    #         tenant_id=tenant_id,
    #         user=request.user,
    #         items_data=serializer.validated_data["items"],
    #     )

    #     # panggil serializer untuk convert
    #     response_serializer = self.get_serializer(order_instance)
    #     return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def void_order(self, request, pk=None):
        """
        kalo manager/owner mau ganti status PAID jadi VOID
        """
        tenant_id = get_current_tenant()

        # panggil service
        void_order_instance = void_order_service(
            tenant_id=tenant_id,
            order_id=pk,
        )

        # balikin ke serializer biar di convert
        response_serializer = self.get_serializer(void_order_instance)
        return Response(data=response_serializer.data, status=status.HTTP_200_OK)
