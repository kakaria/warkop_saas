from .thread_local import clear_thread_local, set_current_tenant


class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_id = request.headers.get("X-Tenant-Id") or request.META.get(
            "HTTP_X_TENANT_ID"
        )
        set_current_tenant(x_id)

        try:
            return self.get_response(request)
        finally:
            clear_thread_local()
