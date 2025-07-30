"""
Middleware pour la gestion des tenants via headers HTTP - Library Service
Aligné avec l'architecture SOA (CRM/Document services)
Compatible avec l'authentification via API Gateway
"""
import uuid
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django_tenants.utils import get_tenant_model
from tenant_schema.models import Client

logger = logging.getLogger('library')

class HeaderTenantMiddleware:
    """
    Middleware pour la gestion des tenants via headers HTTP.
    
    Compatible avec l'API Gateway qui propage l'authentification.
    Les headers X-User-ID, X-User-Email sont propagés par l'API Gateway.
    
    Fonctionnalités:
    1. Validation du tenant_id via tenant-service (avec cache)
    2. Vérification de l'existence locale du tenant
    3. Création contrôlée des tenants si nécessaire
    4. Respect des headers d'authentification propagés
    """
    
    # Endpoints qui ne nécessitent pas de X-Tenant-ID header
    PUBLIC_ENDPOINTS = [
        '/health/',
        '/admin/',
        '/static/',
        '/favicon.ico',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si l'endpoint est public
        if any(request.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            return self.get_response(request)
            
        tenant_id = request.headers.get('X-Tenant-ID')
        
        if not tenant_id:
            return JsonResponse({
                'error': 'Missing X-Tenant-ID header',
                'code': 'missing_tenant_id',
                'service': 'library-service'
            }, status=400)

        try:
            # Nettoyer et valider que c'est un UUID valide
            try:
                # Gérer les en-têtes dupliqués (séparés par des virgules)
                if ',' in tenant_id:
                    # Prendre le premier UUID si plusieurs sont présents
                    tenant_id = tenant_id.split(',')[0].strip()
                    logger.warning(f"Library - En-têtes X-Tenant-ID dupliqués détectés, utilisation du premier: {tenant_id}")
                
                # Nettoyer l'UUID (supprimer espaces, etc.)
                clean_tenant_id = tenant_id.strip()
                tenant_uuid = uuid.UUID(clean_tenant_id)
                # Utiliser l'UUID nettoyé pour la suite
                tenant_id = str(tenant_uuid)
            except ValueError:
                logger.error(f"Library - UUID invalide reçu: '{tenant_id}' (longueur: {len(tenant_id)})")
                return JsonResponse({
                    'error': 'X-Tenant-ID doit être un UUID valide',
                    'code': 'invalid_uuid_format',
                    'service': 'library-service'
                }, status=400)
            
            # Vérifier le cache d'abord
            cache_key = f'library_tenant_info:{tenant_id}'
            tenant_info = cache.get(cache_key)
            
            if not tenant_info:
                # Valider le tenant via tenant-service
                tenant_service_url = getattr(settings, 'TENANT_SERVICE_URL', 'http://localhost:8001')
                response = requests.get(
                    f"{tenant_service_url}/api/tenants/{tenant_id}/",
                    headers={'Accept': 'application/json'},
                    timeout=5
                )
                
                if not response.ok:
                    logger.warning(f"Library - Tenant invalide ou inexistant: {tenant_id}")
                    return JsonResponse({
                        'error': 'Invalid or non-existent tenant',
                        'code': 'invalid_tenant_id',
                        'service': 'library-service'
                    }, status=401)

                tenant_data = response.json()
                tenant_info = {
                    'tenant_uuid': tenant_data.get('id'),
                    'is_active': tenant_data.get('is_active', True),
                    'name': tenant_data.get('name', f"Tenant {tenant_id}"),
                    'schema_name': tenant_data.get('schema_name', f"tenant_{str(tenant_uuid).replace('-', '_')}")
                }
                
                # Mettre en cache pour 30 minutes (pour réduire les appels tenant-service)
                cache.set(cache_key, tenant_info, 1800)
            
            # Vérifier que le tenant est actif
            if not tenant_info.get('is_active'):
                return JsonResponse({
                    'error': 'Tenant is inactive',
                    'code': 'inactive_tenant',
                    'service': 'library-service'
                }, status=403)

            # Récupérer ou créer le tenant localement (contrôlé et sécurisé)
            tenant = self._get_or_create_tenant(tenant_uuid, tenant_info)
            if not tenant:
                logger.error(f"Library - Impossible de configurer le tenant {tenant_id}")
                return JsonResponse({
                    'error': 'Failed to configure tenant in library service',
                    'code': 'tenant_configuration_failed',
                    'service': 'library-service'
                }, status=503)
            
            # Définir le contexte tenant pour la requête
            from django.db import connection
            connection.set_tenant(tenant)
            
            # Ajouter les informations du tenant à la requête
            request.tenant = tenant
            request.tenant_id = tenant_id
            request.tenant_schema = tenant_info['schema_name']
            request.tenant_name = tenant_info['name']
            
            logger.debug(f"Library - Tenant activé: {tenant_id} (schema: {tenant_info['schema_name']})")
            
            response = self.get_response(request)
            
            # Réinitialiser le schéma après la requête
            connection.set_schema_to_public()
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Library - Erreur de connexion au service tenant: {str(e)}")
            return JsonResponse({
                'error': 'Tenant service unavailable',
                'code': 'tenant_service_error',
                'service': 'library-service'
            }, status=503)
            
        except Exception as e:
            logger.error(f"Library - Erreur inattendue dans le middleware: {str(e)}")
            return JsonResponse({
                'error': 'Internal server error',
                'code': 'internal_error',
                'service': 'library-service'
            }, status=500)
    
    def _get_or_create_tenant(self, tenant_uuid, tenant_info):
        """
        Récupère un tenant existant ou le crée de manière contrôlée.
        Compatible avec l'architecture SOA mais sécurisé.
        """
        try:
            # Essayer de récupérer le tenant existant
            tenant = Client.objects.filter(tenant_uuid=tenant_uuid).first()
            if tenant:
                logger.debug(f"Library - Tenant trouvé: {tenant.name}")
                return tenant
            
            # Tenant validé par tenant-service mais inexistant localement
            # Création contrôlée uniquement si validé par tenant-service
            logger.info(f"Library - Création contrôlée du tenant: {tenant_uuid}")
            
            schema_name = tenant_info['schema_name']
            tenant_name = tenant_info['name']
            
            # Éviter les conflits de nom de schéma
            if Client.objects.filter(schema_name=schema_name).exists():
                schema_name = f"tenant_{str(tenant_uuid).replace('-', '_')[:12]}"
            
            # Créer le tenant de manière atomique
            from django.db import transaction
            try:
                with transaction.atomic():
                    tenant = Client.objects.create(
                        tenant_uuid=tenant_uuid,
                        schema_name=schema_name,
                        name=tenant_name,
                        is_active=True
                    )
                    
                    # Exécuter les migrations pour le nouveau schéma
                    from django.core.management import call_command
                    call_command('migrate_schemas', schema_name=schema_name, verbosity=0)
                    
                    logger.info(f"Library - Tenant créé: {tenant_name} (schema: {schema_name})")
                    return tenant
                    
            except Exception as create_error:
                # En cas d'erreur, essayer de récupérer (race condition possible)
                if "duplicate key value violates unique constraint" in str(create_error):
                    logger.debug(f"Library - Race condition détectée pour tenant {tenant_uuid}, récupération...")
                    tenant = Client.objects.filter(tenant_uuid=tenant_uuid).first()
                    if tenant:
                        logger.debug(f"Library - Tenant récupéré après race condition: {tenant.name}")
                        return tenant
                else:
                    logger.warning(f"Library - Erreur création, récupération: {str(create_error)}")
                
                tenant = Client.objects.filter(tenant_uuid=tenant_uuid).first()
                if tenant:
                    return tenant
                raise create_error
                
        except Exception as e:
            logger.error(f"Library - Erreur configuration tenant: {str(e)}")
            return None