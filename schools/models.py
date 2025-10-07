from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    auto_create_schema = True
    
    on_trial = models.BooleanField(default=True)
    paid_until = models.DateField(null=True, blank=True)
    
    # Custom admin credentials
    admin_username = models.CharField(max_length=150, default="schooladmin")
    admin_email = models.EmailField(blank=True)
    admin_password = models.CharField(max_length=128, help_text="Plain text password (will be hashed)")

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass