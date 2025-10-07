from django.contrib.auth.backends import ModelBackend
from django.db import connection
from globals.models import GlobalSuperAdmin

class GlobalAdminAuthBackend(ModelBackend):
    """
    Authenticates against globals.GlobalSuperAdmin in public schema
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Only use in public schema
        if connection.schema_name != 'public':
            return None
        
        # GlobalSuperAdmin uses email, not username
        email = kwargs.get('email') or username
        
        try:
            user = GlobalSuperAdmin.objects.get(email=email)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except GlobalSuperAdmin.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        if connection.schema_name != 'public':
            return None
            
        try:
            return GlobalSuperAdmin.objects.get(pk=user_id)
        except GlobalSuperAdmin.DoesNotExist:
            return None