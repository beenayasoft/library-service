from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain

@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    Administration simplifiée des tenants (clients) - Library Service
    Alignée avec l'architecture SOA
    """
    list_display = ('name', 'schema_name', 'tenant_uuid', 'is_active', 'max_library_items', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'tenant_uuid')
    readonly_fields = ('schema_name', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'tenant_uuid')
        }),
        ('Configuration', {
            'fields': ('is_active', 'max_library_items')
        }),
        ('Métadonnées', {
            'fields': ('schema_name', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """
    Administration simplifiée des domaines - Library Service
    Alignée avec l'architecture SOA
    """
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain', 'tenant__name')
    
    fieldsets = (
        ('Configuration du domaine', {
            'fields': ('domain', 'tenant', 'is_primary')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant')
