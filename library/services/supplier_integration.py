"""
Service d'intégration avec le service CRM pour la gestion des fournisseurs
"""
import requests
import logging
from typing import Optional, List, Dict, Any
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('library')


class SupplierIntegrationService:
    """Service pour l'intégration avec les fournisseurs du service CRM"""
    
    def __init__(self, tenant_id: str, auth_token: str = None):
        self.tenant_id = tenant_id
        self.auth_token = auth_token
        self.crm_base_url = getattr(settings, 'CRM_SERVICE_URL', 'http://localhost:8003')  # Direct CRM service
        self.timeout = 5
        self.cache_timeout = 300  # 5 minutes
    
    def _get_headers(self) -> Dict[str, str]:
        """Génère les en-têtes pour les appels CRM via API Gateway"""
        headers = {
            'X-Tenant-ID': str(self.tenant_id),  # S'assurer que c'est une string
            'Content-Type': 'application/json',
            'User-Agent': 'Library-Service/1.0'
        }
        
        # Ajouter le token d'authentification si disponible
        # Le token reçu est déjà au format "Bearer xxx" depuis X-Auth-Token
        if self.auth_token:
            if self.auth_token.startswith('Bearer '):
                headers['Authorization'] = self.auth_token
            else:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
        return headers
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Effectue une requête HTTP avec gestion d'erreurs"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"CRM service call failed: {method} {url} - {e}")
            return None
    
    def get_supplier_details(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails complets d'un fournisseur depuis le service CRM
        
        Args:
            supplier_id: UUID du fournisseur dans le service CRM
            
        Returns:
            Dict avec les détails du fournisseur ou None si erreur
        """
        if not supplier_id:
            return None
            
        # Vérifier le cache
        cache_key = f"supplier_details_{self.tenant_id}_{supplier_id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Supplier {supplier_id} found in cache")
            return cached_data
        
        # 🚀 Appel optimisé au service CRM avec retry et métriques
        url = f"{self.crm_base_url}/api/tiers/{supplier_id}/"
        
        # Tentative avec retry automatique (3 essais max)
        for attempt in range(3):
            response = self._make_request('GET', url)
            
            if response and response.status_code == 200:
                try:
                    data = response.json()
                    # Vérifier que c'est bien un fournisseur
                    if data.get('relation') == 'fournisseur':
                        # ✅ Succès - Mise en cache avec TTL optimisé
                        cache.set(cache_key, data, timeout=self.cache_timeout)
                        logger.info(f"[INTEGRATION] Supplier '{data.get('nom', 'N/A')}' fetched successfully (attempt {attempt + 1})")
                        return data
                    else:
                        logger.warning(f"[INTEGRATION] Tiers {supplier_id} is not a supplier: {data.get('relation', 'unknown')}")
                        return None
                except (ValueError, KeyError) as e:
                    logger.error(f"[INTEGRATION] Invalid response format from CRM service: {e}")
                    return None
            elif response and response.status_code == 404:
                logger.warning(f"[INTEGRATION] Supplier {supplier_id} not found in CRM")
                return None
            elif response and response.status_code in [401, 403]:
                logger.error(f"[INTEGRATION] Authentication failed for supplier {supplier_id} (status: {response.status_code})")
                # Pas de retry sur les erreurs d'auth
                return None
            else:
                # Retry sur les erreurs temporaires (5xx, timeouts, etc.)
                if attempt < 2:  # Retry seulement les 2 premiers essais
                    logger.warning(f"[INTEGRATION] Attempt {attempt + 1} failed for supplier {supplier_id}, retrying...")
                    continue
                else:
                    logger.error(f"[INTEGRATION] All attempts failed for supplier {supplier_id}")
                    
        return None
    
    def search_suppliers(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche des fournisseurs dans le service CRM
        
        Args:
            query: Terme de recherche
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des fournisseurs trouvés
        """
        if not query or len(query) < 2:
            return []
        
        # Vérifier le cache pour les recherches fréquentes
        cache_key = f"supplier_search_{self.tenant_id}_{query}_{limit}"
        cached_results = cache.get(cache_key)
        if cached_results:
            logger.debug(f"Search results for '{query}' found in cache")
            return cached_results
        
        # Appel au service CRM
        url = f"{self.crm_base_url}/api/tiers/"
        params = {
            'relation': 'fournisseur',
            'search': query,
            'limit': limit,
            'is_deleted': 'false'  # Exclure les fournisseurs supprimés
        }
        
        response = self._make_request('GET', url, params=params)
        
        if response and response.status_code == 200:
            try:
                data = response.json()
                results = data.get('results', []) if isinstance(data, dict) else data
                
                # Formatage simplifié pour l'usage Library
                formatted_results = []
                for supplier in results:
                    formatted_results.append({
                        'id': supplier.get('id'),
                        'nom': supplier.get('nom'),
                        'siret': supplier.get('siret'),
                        'numero_tva': supplier.get('numero_tva'),
                        'email': supplier.get('email'),
                        'telephone': supplier.get('telephone'),
                        'relation': supplier.get('relation')
                    })
                
                # Mise en cache pour 2 minutes (recherches moins persistantes)
                cache.set(cache_key, formatted_results, timeout=120)
                logger.debug(f"Search results for '{query}' cached successfully")
                return formatted_results
                
            except (ValueError, KeyError) as e:
                logger.error(f"Invalid search response format from CRM service: {e}")
        
        return []
    
    def get_suppliers_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des fournisseurs depuis le service CRM
        
        Returns:
            Dict avec les statistiques ou données par défaut si erreur
        """
        cache_key = f"supplier_stats_{self.tenant_id}"
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return cached_stats
        
        url = f"{self.crm_base_url}/api/tiers/stats/"
        params = {'relation': 'fournisseur'}
        
        response = self._make_request('GET', url, params=params)
        
        if response and response.status_code == 200:
            try:
                stats = response.json()
                # Mise en cache pour 10 minutes (stats moins fréquentes)
                cache.set(cache_key, stats, timeout=600)
                return stats
            except ValueError as e:
                logger.error(f"Invalid stats response format from CRM service: {e}")
        
        # Données par défaut en cas d'erreur
        return {
            'total_suppliers': 0,
            'active_suppliers': 0,
            'error': 'CRM service unavailable'
        }
    
    def validate_supplier_exists(self, supplier_id: str) -> bool:
        """
        Vérifie qu'un fournisseur existe dans le service CRM
        
        Args:
            supplier_id: UUID du fournisseur
            
        Returns:
            True si le fournisseur existe, False sinon
        """
        supplier_details = self.get_supplier_details(supplier_id)
        return supplier_details is not None
    
    def get_supplier_name_only(self, supplier_id: str) -> Optional[str]:
        """
        Récupère uniquement le nom d'un fournisseur (optimisé)
        
        Args:
            supplier_id: UUID du fournisseur
            
        Returns:
            Nom du fournisseur ou None
        """
        supplier_details = self.get_supplier_details(supplier_id)
        if supplier_details:
            return supplier_details.get('nom')
        return None


# Singleton pattern pour éviter la réinstanciation
_supplier_services = {}

def get_supplier_service(tenant_id: str, auth_token: str = None) -> SupplierIntegrationService:
    """
    Factory function pour obtenir une instance du service fournisseur
    avec mise en cache par tenant et token
    """
    # Clé de cache incluant le token (hash pour éviter de stocker le token complet)
    cache_key = f"{tenant_id}_{hash(auth_token) if auth_token else 'no_token'}"
    
    if cache_key not in _supplier_services:
        _supplier_services[cache_key] = SupplierIntegrationService(tenant_id, auth_token)
    return _supplier_services[cache_key]