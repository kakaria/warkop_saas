from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import (
    BusinessRuleViolation,
    ProductNotFoundError,
    ResourceNotFound,
)
from core.thread_local import get_current_tenant
from products.dto import CreateProductDTO
from products.models import Product
from products.serializers import (
    ProductBasicPatchSerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    StockAdjustmentSerializer,
    StockMovementDetailSerializer,
    StockMovementListSerializer,
)
from products.services import (
    adjust_stock_service,
    archive_product_service,
    create_product_service,
    fetch_stock_movement_product_service,
    list_stock_movement,
    unarchived_product_service,
)
from tenants.models import TenantMembership
from tenants.permissions import IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner
from tenants.services import get_current_active_membership


class ProductCreateAPIView(APIView):
    # panggil permission
    permission_classes = [IsAuthenticatedAndHasTenant]

    def post(self, request, *args, **kwargs) -> Response:
        # panggil input serializer
        input_serializer = ProductCreateSerializer(data=request.data)

        # validasi input_serializer
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        # ambil tenant_id
        tenant_id = get_current_tenant()

        # panggil CreateProductDTO
        dto = CreateProductDTO(
            name=validated_data["name"],
            price=validated_data["price"],
            stock=validated_data["stock"],
        )

        # ambil si actor membership (yang lagi panggil endpoint ini)
        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=tenant_id,
        )

        # panggil service
        product = create_product_service(
            actor_membership=actor_membership,
            data=dto,
        )

        # panggil output serializer
        response_serializer = ProductDetailSerializer(product)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ProductListAPIView(ListAPIView):

    # permission_classes
    permission_classes = [IsAuthenticatedAndHasTenant]

    # serializer
    serializer_class = ProductListSerializer

    # override
    def get_queryset(self):
        return Product.objects.all()


class ProductRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticatedAndHasTenant]

    serializer_class = ProductDetailSerializer

    def get_queryset(self):

        return Product.objects.all()


# view untuk patch (data mutation) gak ada efek domino ke sistem lain
class ProductBasicPatchView(UpdateAPIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    serializer_class = ProductBasicPatchSerializer

    http_method_names = ["patch"]

    def get_queryset(self):
        tenant_id = get_current_tenant()

        if tenant_id is None:
            return Product.objects.none()

        return Product.objects.filter(tenant_id=tenant_id, is_archived=False)


class StockAdjustmentAPIView(APIView):

    # permission
    permission_classes = [IsAuthenticatedAndHasTenant]

    def post(self, request, product_id):

        # pasang input serializer
        input_serializer = StockAdjustmentSerializer(data=request.data)
        # validasi input serializer
        input_serializer.is_valid(raise_exception=True)

        tenant_id = get_current_tenant()

        if tenant_id is None:
            raise ValidationError("Tenant contex is required!")

        # ambil tenant_membership dari request.user
        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=tenant_id,
        )

        try:

            # panggil service
            stock_movement = adjust_stock_service(
                actor_membership=actor_membership,
                product_id=product_id,
                validated_data=input_serializer.validated_data,
            )
        except ProductNotFoundError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_404_NOT_FOUND,
            )

        # panggil ouput serializer
        output_serializer = StockMovementDetailSerializer(stock_movement)

        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class StockMovementDetailAPIView(APIView):

    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get(self, request, product_id):

        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        stock_movement = fetch_stock_movement_product_service(
            actor_membership=actor_membership,
            product_id=product_id,
        )

        output_serializer = StockMovementDetailSerializer(stock_movement, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class StockMovementByProductListAPIView(APIView):
    permission_classes = [IsAuthenticatedAndHasTenant, IsTenantManagerOrOwner]

    def get(self, request):

        actor_membership = get_current_active_membership(
            user=request.user, tenant_id=get_current_tenant()
        )

        stock_movement = list_stock_movement(
            actor_membership=actor_membership,
        )

        output_serializer = StockMovementListSerializer(stock_movement, many=True)

        return Response(output_serializer.data, status=status.HTTP_200_OK)


class ArchiveProductAPIView(APIView):

    permission_classes = [IsAuthenticatedAndHasTenant]

    http_method_names = ["delete"]

    def delete(self, request, product_id, format=None):

        try:
            actor_membership = get_current_active_membership(
                user=request.user, tenant_id=get_current_tenant()
            )
        except TenantMembership.DoesNotExist:
            raise ResourceNotFound("Membership tidak ditemukan!")

        # panggil service
        archive_product_service(
            actor_membership=actor_membership, product_id=product_id
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class UnarchiveProductAPIView(APIView):

    permission_classes = [IsAuthenticatedAndHasTenant]

    def post(self, request, product_id):

        # cek membership user
        try:
            actor_membership = get_current_active_membership(
                user=request.user, tenant_id=get_current_tenant()
            )
        except TenantMembership.DoesNotExist:
            raise ResourceNotFound("Membership tidak ditemukan!")

        # panggil service
        unarchived_product_service(
            actor_membership=actor_membership, product_id=product_id
        )

        return Response(
            {"detail": "Product telah dipulihkan"}, status=status.HTTP_200_OK
        )
