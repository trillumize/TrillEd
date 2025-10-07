from django.contrib import admin
from django.db import connection

class TenantAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set admin site name based on schema
        if request.path.startswith('/admin/'):
            if connection.schema_name == 'public':
                admin.site.site_header = "Global Administration"
                admin.site.site_title = "Global Admin"
            else:
                admin.site.site_header = f"{connection.tenant.name} Administration"
                admin.site.site_title = f"{connection.tenant.name} Admin"
        
        response = self.get_response(request)
        return response