from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.thread_local import get_current_tenant
from products.models import Product
from products.serializers import ProductCreateSerializer, ProductDetailSerializer
from products.services import create_product_service
from tenants.permissions import IsAuthenticatedAndHasTenant
from tenants.services import get_current_active_membership


class ProductCreateAPIView(APIView):
    # panggil permission
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs) -> Response:
        # panggil input serializer
        input_serializer = ProductCreateSerializer(data=request.data)

        # validasi input_serializer
        input_serializer.is_valid(raise_exception=True)

        validated_data = input_serializer.validated_data

        # ambil tenant_id
        tenant_id = get_current_tenant()

        if tenant_id is None:
            raise ValidationError("Tenant context is required!")

        # ambil si actor membership (yang lagi panggil endpoint ini)
        actor_membership = get_current_active_membership(
            user=request.user,
            tenant_id=tenant_id,
        )

        # panggil service
        product = create_product_service(
            actor_membership=actor_membership,
            validated_data=validated_data,
        )

        # panggil output serializer
        response_serializer = ProductDetailSerializer(product)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class ProductListAPIView(ListAPIView):

    # permission_classes
    permission_classes = [IsAuthenticated]

    # serializer
    serializer_class = ProductDetailSerializer

    # override
    def get_queryset(self):
        tenant_id = get_current_tenant()

        if tenant_id is None:
            raise ValidationError("Tenant context is required!")

        return Product.objects.all()


class ProductRetrieveAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticatedAndHasTenant]

    serializer_class = ProductDetailSerializer

    def get_queryset(self):

        return Product.objects.all()
