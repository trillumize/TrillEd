from django.contrib import admin
from django.shortcuts import render, redirect
from django_tenants.utils import schema_context
from .models import Client, Domain
from accounts.models import User
from django_tenants.admin import TenantAdminMixin
from django.db import connection
from django.contrib import messages


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "admin_username", "paid_until", "on_trial", "created_on")
    search_fields = ("name", "admin_username")
    
    # Show the credential fields in the form
    fields = (
        'name', 
        'schema_name',
        'admin_username',
        'admin_email', 
        'admin_password',
        'on_trial', 
        'paid_until'
    )

    def save_model(self, request, obj, form, change):
        # Check if this is a new client or password was changed
        creating_new = obj.pk is None
        password_changed = 'admin_password' in form.changed_data
        
        super().save_model(request, obj, form, change)
        obj.create_schema(check_if_exists=True)

        # Create or update admin user if new client or password changed
        if creating_new or password_changed:
            with schema_context(obj.schema_name):
                # Delete existing admin if any
                User.objects.filter(username=obj.admin_username).delete()
                
                # Create new admin with custom credentials
                admin_user = User.objects.create_superuser(
                    username=obj.admin_username,
                    email=obj.admin_email or f"{obj.schema_name}@school.com",
                    password=obj.admin_password,  # This will be hashed by create_superuser
                    first_name="School",
                    last_name="Admin",
                )
                admin_user.is_staff = True
                admin_user.is_superuser = True
                admin_user.role = "school_admin"
                admin_user.save()
                
                messages.success(
                    request, 
                    f"School admin created - Username: {obj.admin_username}"
                )

    # Restrict to public schema only
    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")

    def has_module_permission(self, request):
        return connection.schema_name == 'public'

    def has_view_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_add_permission(self, request):
        return connection.schema_name == 'public'

    def has_change_permission(self, request, obj=None):
        return connection.schema_name == 'public'

    def has_delete_permission(self, request, obj=None):
        return connection.schema_name == 'public'