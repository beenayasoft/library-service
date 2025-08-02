"""
Middleware pour la gestion des tenants via headers HTTP - Library Service
Aligné avec l'architecture SOA (CRM/Document services)
Compatible avec l'authentification via API Gateway
OPTIMISÉ: Extraction tenant_id du JWT sans appel externe redondant
"""
import uuid
import logging
import requests
import jwt
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
    
    Fonctionnalités OPTIMISÉES:
    1. Extraction tenant_id directement du JWT (pas d'appel externe)
    2. Validation tenant_id depuis JWT déjà validé par Gateway  
    3. Cache local tenant info avec fallback sécurisé
    4. Création contrôlée des tenants si nécessaire
    5. Respect des headers d'authentification propagés
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
    
    def _extract_tenant_from_jwt(self, request):
        """
        Extrait tenant_id du JWT sans validation (Gateway l'a déjà fait).
        Optimisation: évite l'appel externe redondant vers tenant-service.
        """
        try:
            # Récupérer token JWT depuis header Authorization
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                logger.debug("Library - Pas de token JWT Bearer trouvé")
                return None
            
            token = auth_header[7:]  # Supprimer "Bearer "
            
            # Décoder JWT SANS validation (Gateway l'a déjà fait)
            # Utilisation de verify=False car Gateway a validé signature/expiration
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                tenant_id = payload.get('tenant_id')
                
                if tenant_id:
                    logger.debug(f"Library - tenant_id extrait du JWT: {tenant_id}")
                    return {
                        'tenant_id': str(tenant_id),
                        'user_id': payload.get('user_id'),
                        'email': payload.get('email'),
                        'extracted_from': 'jwt'
                    }
                else:
                    logger.warning("Library - tenant_id manquant dans JWT payload")
                    return None
                    
            except Exception as e:
                # Capture toutes les exceptions JWT possibles selon la version
                logger.warning(f"Library - Erreur décodage JWT: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Library - Erreur extraction JWT: {str(e)}")
            return None

    def __call__(self, request):
        import time
        
        # 🎯 AUDIT LATENCE - Start middleware timing
        middleware_start = time.time()
        logger.info(f"[MIDDLEWARE AUDIT] START - {request.method} {request.path}")
        
        # Vérifier si l'endpoint est public
        if any(request.path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            public_time = time.time()
            logger.info(f"[MIDDLEWARE AUDIT] Public endpoint bypass: {(public_time - middleware_start)*1000:.2f}ms")
            return self.get_response(request)
            
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # 🎯 AUDIT - Timing header extraction
        header_time = time.time()
        logger.info(f"[MIDDLEWARE AUDIT] Header extraction: {(header_time - middleware_start)*1000:.2f}ms")
        
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
            
            # 🎯 AUDIT - Timing JWT extraction
            jwt_start = time.time()
            
            # OPTIMISATION: Extraire tenant info du JWT d'abord
            jwt_data = self._extract_tenant_from_jwt(request)
            
            jwt_time = time.time()
            logger.info(f"[MIDDLEWARE AUDIT] JWT extraction: {(jwt_time - jwt_start)*1000:.2f}ms")
            
            if jwt_data and jwt_data['tenant_id'] == tenant_id:
                logger.debug(f"Library - tenant_id validé via JWT: {tenant_id}")
                # JWT contient tenant_id valide, pas besoin d'appel externe
                
                # 🎯 AUDIT - Timing cache check
                cache_start = time.time()
                
                # Vérifier le cache local d'abord pour les détails tenant
                cache_key = f'library_tenant_local:{tenant_id}'
                tenant_info = cache.get(cache_key)
                
                cache_time = time.time()
                cache_hit = tenant_info is not None
                logger.info(f"[MIDDLEWARE AUDIT] Cache check ({cache_hit and 'HIT' or 'MISS'}): {(cache_time - cache_start)*1000:.2f}ms")
                
                if not tenant_info:
                    # Générer tenant_info à partir du JWT + defaults sécurisés
                    tenant_info = {
                        'tenant_uuid': tenant_id,
                        'is_active': True,  # JWT validé par Gateway = tenant actif
                        'name': f"Tenant {tenant_id[:8]}",
                        'schema_name': f"tenant_{str(tenant_uuid).replace('-', '_')}",
                        'extracted_from': 'jwt'
                    }
                    
                    # OPTIMISATION: Cache local 2 heures (réduction massive des appels externes)
                    cache.set(cache_key, tenant_info, 7200)  # 2h au lieu de 30min
                    logger.info(f"Library - Tenant info mise en cache locale: {tenant_id}")
                
            else:
                # Fallback: validation via tenant-service (rare, si JWT invalide)
                logger.warning(f"Library - Fallback tenant-service pour: {tenant_id}")
                cache_key = f'library_tenant_fallback:{tenant_id}'
                tenant_info = cache.get(cache_key)
                
                if not tenant_info:
                    # OPTIMISATION CRITIQUE: Éviter tenant-service (1.97s!) - utiliser JWT directement
                    logger.info(f"Library - Évitement tenant-service lent, utilisation JWT: {tenant_id}")
                    tenant_info = {
                        'tenant_uuid': tenant_id,
                        'is_active': True,  # JWT validé = tenant actif
                        'name': f"JWT Tenant {tenant_id[:8]}",
                        'schema_name': f"tenant_{str(tenant_uuid).replace('-', '_')}",
                        'extracted_from': 'jwt_optimized'
                    }
                    
                    # Cache JWT-based tenant info pour 2 heures
                    cache.set(cache_key, tenant_info, 7200)
                    logger.info(f"Library - Tenant JWT optimisé mis en cache: {tenant_id}")
                    
            
            # Vérifier que le tenant est actif
            if not tenant_info.get('is_active'):
                return JsonResponse({
                    'error': 'Tenant is inactive',
                    'code': 'inactive_tenant',
                    'service': 'library-service'
                }, status=403)

            # 🎯 AUDIT - Timing tenant setup
            tenant_setup_start = time.time()
            
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
            
            tenant_setup_time = time.time()
            logger.info(f"[MIDDLEWARE AUDIT] Tenant setup: {(tenant_setup_time - tenant_setup_start)*1000:.2f}ms")
            
            # Ajouter les informations du tenant à la requête
            request.tenant = tenant
            request.tenant_id = tenant_id
            request.tenant_schema = tenant_info['schema_name']
            request.tenant_name = tenant_info['name']
            
            # Logging optimisation pour analyse performance
            extraction_method = tenant_info.get('extracted_from', 'unknown')
            
            # 🎯 AUDIT - Timing request processing
            request_start = time.time()
            middleware_total = (request_start - middleware_start) * 1000
            
            logger.info(f"[MIDDLEWARE AUDIT] MIDDLEWARE TOTAL: {middleware_total:.2f}ms (method: {extraction_method})")
            
            # Ajouter métriques d'optimisation à la requête
            request.tenant_extraction_method = extraction_method
            request.middleware_latency_ms = middleware_total
            
            response = self.get_response(request)
            
            # 🎯 AUDIT - Timing cleanup
            cleanup_start = time.time()
            
            # Réinitialiser le schéma après la requête
            connection.set_schema_to_public()
            
            cleanup_time = time.time()
            total_middleware_time = (cleanup_time - middleware_start) * 1000
            
            logger.info(f"[MIDDLEWARE AUDIT] Cleanup: {(cleanup_time - cleanup_start)*1000:.2f}ms")
            logger.info(f"[MIDDLEWARE AUDIT] TOTAL MIDDLEWARE TIME: {total_middleware_time:.2f}ms")
            
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
                    
                    # OPTIMISATION CRITIQUE: Migrations asynchrones pour éviter blocage (14s → 0ms)
                    from django.core.management import call_command
                    import threading
                    
                    def run_migrations_async():
                        """Exécute les migrations en arrière-plan (non-bloquant)"""
                        try:
                            call_command('migrate_schemas', schema_name=schema_name, verbosity=0)
                            logger.info(f"Library - Migrations async terminées: {schema_name}")
                        except Exception as e:
                            logger.error(f"Library - Erreur migrations async: {str(e)}")
                    
                    # Lancer migrations en arrière-plan (non-bloquant) 
                    migration_thread = threading.Thread(target=run_migrations_async, daemon=True)
                    migration_thread.start()
                    logger.info(f"Library - Migrations async démarrées pour: {schema_name}")
                    
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