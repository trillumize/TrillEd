from django.contrib.auth.backends import ModelBackend
from django.db import connection
from accounts.models import User

class TenantAuthBackend(ModelBackend):
    """
    Authenticates against accounts.User in tenant schemas
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Only use this backend if we're in a tenant schema
        if connection.schema_name == 'public':
            return None
            
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        if connection.schema_name == 'public':
            return None
            
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None