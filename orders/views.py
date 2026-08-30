from rest_framework import status
from rest_framework.generics import ListAPIView
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

from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderPaidSerializer,
    OrderVoidSerializer,
)


class OrderCreateAPIView(APIView):

    permission_classes = [IsAuthenticatedAndHasTenant]

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


class OrderListAPIView(ListAPIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get_queryset(self):
        actor_membership = get_current_active_membership(
            user=self.request.user, tenant_id=get_current_tenant()
        )

        # langsung panggil service
        return list_order_service(
            actor_membership=actor_membership,
        )


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
            user=request.user, tenant_id=get_current_tenant()
        )
        order = order_paid_service(actor_membership=actor_membership, order_id=order_id)

        output_serializer = OrderDetailSerializer(order)

        return Response(output_serializer.data, status=status.HTTP_200_OK)
