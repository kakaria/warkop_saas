from .thread_local import set_current_tenant, clear_thread_local

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        
        x_id = request.headers.get('X-TENANT-ID')
        
        if x_id:
            set_current_tenant(x_id)
        else:
            set_current_tenant(None)
            
        try:
            response =  self.get_response(request)
            return response
        finally:
            clear_thread_local()
    
    