"""
Mixins utilitaires pour les ViewSets du service library
Gestion de l'authentification via headers propagés par l'API Gateway
"""
import logging

logger = logging.getLogger('library')

class GatewayAuthMixin:
    """
    Mixin pour récupérer les informations d'authentification depuis les headers
    propagés par l'API Gateway (X-User-ID, X-Tenant-ID, X-User-Email)
    """
    
    def get_current_user_info(self):
        """
        Récupère les informations de l'utilisateur actuel depuis les headers HTTP
        propagés par l'API Gateway
        """
        user_info = {
            'user_id': self.request.META.get('HTTP_X_USER_ID'),
            'tenant_id': self.request.META.get('HTTP_X_TENANT_ID'),
            'user_email': self.request.META.get('HTTP_X_USER_EMAIL'),
            'is_authenticated': False
        }
        
        # Considérer l'utilisateur comme authentifié s'il a un user_id et tenant_id
        if user_info['user_id'] and user_info['tenant_id']:
            user_info['is_authenticated'] = True
            logger.debug(f"Library - User authenticated: {user_info['user_email']} (ID: {user_info['user_id']})")
        else:
            logger.debug("Library - No user authentication headers found")
        
        return user_info
    
    def get_tenant_info(self):
        """
        Récupère les informations du tenant depuis la requête
        (injectées par le middleware HeaderTenantMiddleware)
        """
        tenant_info = {
            'tenant_id': getattr(self.request, 'tenant_id', None),
            'tenant_schema': getattr(self.request, 'tenant_schema', None),
            'tenant_name': getattr(self.request, 'tenant_name', None),
            'tenant_obj': getattr(self.request, 'tenant', None)
        }
        
        if tenant_info['tenant_id']:
            logger.debug(f"Library - Tenant context: {tenant_info['tenant_name']} ({tenant_info['tenant_schema']})")
        
        return tenant_info
    
    def log_request_context(self, action="unknown"):
        """
        Log le contexte de la requête pour debugging
        """
        user_info = self.get_current_user_info()
        tenant_info = self.get_tenant_info()
        
        logger.info(
            f"Library - Action: {action}, "
            f"User: {user_info.get('user_email', 'Anonymous')}, "
            f"Tenant: {tenant_info.get('tenant_name', 'Unknown')}"
        )
    
    def perform_create(self, serializer):
        """
        Override pour logger les créations avec contexte utilisateur
        """
        self.log_request_context("create")
        super().perform_create(serializer)
    
    def perform_update(self, serializer):
        """
        Override pour logger les mises à jour avec contexte utilisateur
        """
        self.log_request_context("update")
        super().perform_update(serializer)
    
    def perform_destroy(self, instance):
        """
        Override pour logger les suppressions avec contexte utilisateur
        """
        self.log_request_context("delete")
        super().perform_destroy(instance)