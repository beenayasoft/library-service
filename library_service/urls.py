"""
URL configuration for library_service project.
Service de bibliothèque d'ouvrages BTP avec support multi-tenant.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def health_check(request):
    """Endpoint de vérification de l'état du service"""
    tenant_info = "N/A"
    if hasattr(request, 'tenant') and request.tenant:
        tenant_info = f"{request.tenant.name} ({request.tenant.schema_name})"
    
    return JsonResponse({
        'service': 'library-service',
        'status': 'healthy',
        'version': '1.0.0',
        'tenant': tenant_info
    })

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),
    
    # Health check endpoint
    path('health/', health_check, name='health-check'),
    
    # API de la bibliothèque
    path('api/', include('library.urls')),
]

# Servir les fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
