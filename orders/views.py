from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.thread_local import get_current_tenant
from orders.dto import CreateOrderDTO, OrderItemDTO
from orders.services import create_order_service
from tenants.services import get_current_active_membership

from .models import Order
from .serializers import OrderCreateSerializer, OrderDetailSerializer

# class OrderViewSet(
#     # mixins.CreateModelMixin,
#     mixins.ListModelMixin,
#     mixins.RetrieveModelMixin,
#     viewsets.GenericViewSet,
# ):
#     # biar muncul pas kita GET
#     queryset = Order.objects.all()
#     serializer_class = OrderCreateSerializer

#     # def get_permissions(self):  # setting permission
#     #     if self.action == "void_order":
#     #         return [IsTenantManagerOrOwner()]
#     #     return [IsTenantCashier()]

#     # def create(self, request, *args, **kwargs):

#     #     # panggil serializer CreateOrderSerializer
#     #     serializer = self.get_serializer(data=request.data)
#     #     serializer.is_valid(raise_exception=True)

#     #     # ambil tenant
#     #     tenant_id = get_current_tenant()

#     #     # ambil data bersih (items) terus panggil service layer
#     #     order_instance = process_checkout(
#     #         tenant_id=tenant_id,
#     #         user=request.user,
#     #         items_data=serializer.validated_data["items"],
#     #     )

#     #     # panggil serializer untuk convert
#     #     response_serializer = self.get_serializer(order_instance)
#     #     return Response(data=response_serializer.data, status=status.HTTP_201_CREATED)

#     # @action(detail=True, methods=["post"])
#     # def void_order(self, request, pk=None):
#     #     """
#     #     kalo manager/owner mau ganti status PAID jadi VOID
#     #     """
#     #     tenant_id = get_current_tenant()

#     #     # panggil service
#     #     void_order_instance = void_order_service(
#     #         tenant_id=tenant_id,
#     #         order_id=pk,
#     #     )

#     #     # balikin ke serializer biar di convert
#     #     response_serializer = self.get_serializer(void_order_instance)
#     #     return Response(data=response_serializer.data, status=status.HTTP_200_OK)


class OrderCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        # panggil input serializer
        input_serializer = OrderCreateSerializer(data=request.data)
        # validasi input
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        items = tuple(
            OrderItemDTO(product_id=item["product_id"], quantity=item["quantity"])
            for item in validated_data["items"]
        )

        order_data = CreateOrderDTO(items=items)

        tenant_id = get_current_tenant()

        if tenant_id is None:
            raise ValidationError("Tenant Context is required.")

        # ambil tenant membership pake helper
        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=tenant_id,
        )
        # panggil service
        order = create_order_service(
            actor_membership=actor_membership,
            data=order_data,
        )

        # output serializer
        output_serializer = OrderDetailSerializer(order)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
