from drf_spectacular.utils import OpenApiParameter

TENANT_HEADER = OpenApiParameter(
    name="X-Tenant-Id",
    type=int,
    location=OpenApiParameter.HEADER,
    required=True,
    description="ID of the tenant this request acts on.",
)
