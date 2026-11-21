from drf_spectacular.utils import OpenApiParameter

TENANT_HEADER = OpenApiParameter(
    name="X-Tenant-Id",
    type=int,
    location=OpenApiParameter.HEADER,
    required=True,
    description="ID of the tenant this request acts on.",
)


PUBLIC_PATHS = {
    "/api/v1/tenants/register/",
    "/api/v1/tenants/login/",
    "/api/v1/tenants/refresh/",
}
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def add_tenant_header(result, generator, request, public):
    """Tambahkan header X-Tenant-Id ke semua operasi kecuali endpoint publik."""
    for path, operations in result.get("paths", {}).items():
        if path in PUBLIC_PATHS:
            continue
        for method, operation in operations.items():
            if method not in HTTP_METHODS:
                continue
            params = operation.setdefault("parameters", [])
            if any(p.get("name") == "X-Tenant-Id" for p in params):
                continue
            params.append(
                {
                    "name": "X-Tenant-Id",
                    "in": "header",
                    "required": True,
                    "schema": {"type": "integer"},
                    "description": "ID of the tenant this request acts on.",
                }
            )
    return result
