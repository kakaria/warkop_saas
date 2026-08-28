from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.thread_local import get_current_tenant
from reports.serializers import TodayProductSerializer, TodayStockMovementSerializer
from reports.services import (
    get_today_order_count_service,
    get_today_product_sales_service,
    get_today_stock_movement_service,
)
from tenants.permissions import IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner
from tenants.services import get_current_active_membership


class TodayOrderCountAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant]

    def get(self, request):
        # ambil actor
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        # panggil service
        count = get_today_order_count_service(
            actor_membership=actor_membership,
            now=timezone.now(),
        )

        return Response({"count": count}, status=status.HTTP_200_OK)


class TodayProductSalesAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant]

    def get(self, request):
        # ambil actor
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        # panggil service
        data = get_today_product_sales_service(
            actor_membership=actor_membership,
            now=timezone.now(),
        )

        # output serializer
        output_serializer = TodayProductSerializer(data, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class TodayStockMovementAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get(self, request):
        # ambil actor
        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        # panggil service
        data = get_today_stock_movement_service(
            actor_membership=actor_membership,
            now=timezone.now(),
        )

        # output serializer
        output_serializer = TodayStockMovementSerializer(data, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)



