# import threading

# _thread_local = threading.local()


# def set_current_tenant(tenant_id):
#     _thread_local.tenant_id = tenant_id


# def get_current_tenant():
#     return getattr(_thread_local, "tenant_id", None)


# def clear_thread_local():
#     if hasattr(_thread_local, "tenant_id"):
#         del _thread_local.tenant_id


import threading

_thread_local = threading.local()


# Change return type from -> int to -> None (since this function doesn't return anything)
def set_current_tenant(tenant_id: int | str | None) -> None:
    if tenant_id is not None:
        try:
            # Crucial: Convert the HTTP header string (e.g. "12") into a real integer!
            _thread_local.tenant_id = int(tenant_id)
        except (ValueError, TypeError):
            # If someone sends an invalid header like X-Tenant-Id: "abc", default to None
            _thread_local.tenant_id = None
    else:
        _thread_local.tenant_id = None


# Change return type to -> int | None because it CAN realistically return None
def get_current_tenant() -> int | None:
    return getattr(_thread_local, "tenant_id", None)


def clear_thread_local() -> None:
    if hasattr(_thread_local, "tenant_id"):
        del _thread_local.tenant_id
