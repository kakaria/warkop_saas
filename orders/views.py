from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.thread_local import get_current_tenant
from orders.dto import CreateOrderDTO, OrderItemDTO, VoidOrderDTO
from orders.services import (
    create_order_service,
    fetch_order_service,
    list_order_service,
    order_paid_service,
    order_void_service,
)
from tenants.permissions import IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner
from tenants.services import get_current_active_membership

from .models import Order
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderPaidSerializer,
    OrderVoidSerializer,
)

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


# class Order
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


class OrderListAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get(self, request, format=None):
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        # panggil service
        orders = list_order_service(
            actor_membership=actor_membership,
        )

        # output serializer
        output_serializer = OrderListSerializer(orders, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class OrderDetailAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get(
        self,
        request,
        order_id,
    ):
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        # panggil service
        order = fetch_order_service(
            actor_membership=actor_membership, order_id=order_id
        )

        # output serializer
        output_serializer = OrderDetailSerializer(order)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class OrderVoidAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def post(self, request, order_id):
        input_serializer = OrderVoidSerializer(data=request.data)

        # validasi
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data

        tenant_id = get_current_tenant()

        # ambil membership
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=tenant_id
        )

        data = VoidOrderDTO(
            reason=validated_data["reason"],
            notes=validated_data["notes"],
        )

        # panggil service
        void_order = order_void_service(
            actor_membership=actor_membership, data=data, order_id=order_id
        )

        # output
        output_serializer = OrderDetailSerializer(void_order)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class OrderPaidAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def post(self, request, order_id):
        input_serializer = OrderPaidSerializer(data=request.data)

        input_serializer.is_valid(raise_exception=True)

        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=get_current_tenant()

        )
        order = order_paid_service(
            actor_membership=actor_membership,
            order_id=order_id
        )

        output_serializer = OrderDetailSerializer(order)

        return Response(output_serializer.data, status=status.HTTP_200_OK)
