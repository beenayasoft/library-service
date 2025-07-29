"""
Middleware personnalisé pour le service library-service.
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging

logger = logging.getLogger('library')

class TenantHeaderMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les en-têtes X-Tenant-ID et ajouter des informations 
    sur le tenant dans la réponse.
    """
    
    def process_request(self, request):
        """
        Traite la requête entrante pour extraire le tenant ID.
        """
        # Récupérer le tenant ID depuis l'en-tête
        tenant_id = request.META.get('HTTP_X_TENANT_ID')
        
        if tenant_id:
            request.tenant_id = tenant_id
            logger.debug(f"Tenant ID détecté: {tenant_id}")
        else:
            request.tenant_id = None
            
        return None
    
    def process_response(self, request, response):
        """
        Traite la réponse pour ajouter des en-têtes informatifs.
        """
        # Ajouter l'en-tête du service
        response['X-Service'] = 'library-service'
        response['X-Version'] = '1.0.0'
        
        # Ajouter l'information du tenant si disponible
        if hasattr(request, 'tenant') and request.tenant:
            response['X-Tenant-Schema'] = request.tenant.schema_name
            response['X-Tenant-Name'] = request.tenant.name
        elif hasattr(request, 'tenant_id') and request.tenant_id:
            response['X-Tenant-ID'] = request.tenant_id
            
        return response

class HealthCheckMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les health checks rapidement sans passer par django-tenants.
    """
    
    def process_request(self, request):
        """
        Court-circuite le traitement pour les health checks.
        """
        if request.path_info == '/health/':
            tenant_info = "N/A"
            if hasattr(request, 'tenant') and request.tenant:
                tenant_info = request.tenant.name
            elif hasattr(request, 'tenant_id') and request.tenant_id:
                tenant_info = request.tenant_id
            
            return JsonResponse({
                'service': 'library-service',
                'status': 'healthy',
                'version': '1.0.0',
                'tenant': tenant_info
            })
        
        return None

class CORSMiddleware(MiddlewareMixin):
    """
    Middleware CORS personnalisé pour le service library.
    Complète la configuration django-cors-headers avec des headers spécifiques.
    """
    
    def process_response(self, request, response):
        """
        Ajoute les en-têtes CORS spécifiques au service.
        """
        # Permettre les en-têtes personnalisés dans les requêtes preflight
        if request.method == 'OPTIONS':
            response['Access-Control-Allow-Headers'] = (
                'accept, accept-encoding, authorization, content-type, '
                'dnt, origin, user-agent, x-csrftoken, x-requested-with, '
                'x-tenant-id'
            )
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Max-Age'] = '86400'  # 24 heures
        
        return response

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware pour logger les requêtes avec informations du tenant.
    """
    
    def process_request(self, request):
        """
        Log les détails de la requête.
        """
        tenant_info = "unknown"
        if hasattr(request, 'tenant') and request.tenant:
            tenant_info = f"{request.tenant.name} ({request.tenant.schema_name})"
        elif hasattr(request, 'tenant_id') and request.tenant_id:
            tenant_info = request.tenant_id
        
        logger.info(
            f"Request: {request.method} {request.path_info} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')} "
            f"tenant: {tenant_info}"
        )
        
        return None

class ErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les erreurs de manière cohérente.
    """
    
    def process_exception(self, request, exception):
        """
        Traite les exceptions non gérées.
        """
        tenant_info = "unknown"
        if hasattr(request, 'tenant') and request.tenant:
            tenant_info = f"{request.tenant.name} ({request.tenant.schema_name})"
        elif hasattr(request, 'tenant_id') and request.tenant_id:
            tenant_info = request.tenant_id
        
        logger.error(
            f"Unhandled exception in {request.method} {request.path_info} "
            f"tenant: {tenant_info} - {str(exception)}",
            exc_info=True
        )
        
        # Laisser Django gérer l'exception normalement
        return None