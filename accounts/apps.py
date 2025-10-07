# accounts/apps.py
from django.apps import AppConfig
from django.conf import settings
from django.db import connection
from django_tenants.utils import get_public_schema_name

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        try:
            if connection.schema_name != get_public_schema_name():
                settings.AUTH_USER_MODEL = "accounts.User"
        except Exception:
            pass
