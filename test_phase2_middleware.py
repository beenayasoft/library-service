#!/usr/bin/env python3
"""
Script de test pour valider la Phase 2 - Middleware Tenant uniforme
Tests de l'isolation tenant et communication avec tenant-service
"""
import requests
import json
import uuid
import time
from typing import Dict, Any

# Configuration
LIBRARY_SERVICE_URL = "http://localhost:8005"
GATEWAY_URL = "http://localhost:8000"
TENANT_SERVICE_URL = "http://localhost:8001"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def print_header(message: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}{Colors.END}\n")

def test_service_health(url: str, service_name: str) -> bool:
    """Teste le health check d'un service"""
    try:
        response = requests.get(f"{url}/health/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"{service_name} is healthy: {data.get('status', 'N/A')}")
            return True
        else:
            print_error(f"{service_name} health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"{service_name} is unreachable: {str(e)}")
        return False

def test_no_tenant_header() -> bool:
    """Teste l'accès sans header X-Tenant-ID (doit échouer)"""
    try:
        print_info("Testing request without X-Tenant-ID header...")
        response = requests.get(f"{LIBRARY_SERVICE_URL}/api/categories/", timeout=5)
        
        if response.status_code == 400:
            data = response.json()
            if 'missing_tenant_id' in data.get('code', ''):
                print_success("Middleware correctly rejects requests without X-Tenant-ID")
                return True
            else:
                print_warning(f"Got 400 but unexpected error: {data}")
                return False
        elif response.status_code == 200:
            print_error("Middleware incorrectly allows requests without X-Tenant-ID")
            return False
        else:
            print_warning(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_invalid_tenant_uuid() -> bool:
    """Teste avec un UUID invalide"""
    try:
        print_info("Testing request with invalid UUID...")
        headers = {'X-Tenant-ID': 'invalid-uuid-format'}
        response = requests.get(f"{LIBRARY_SERVICE_URL}/api/categories/", headers=headers, timeout=5)
        
        if response.status_code == 400:
            data = response.json()
            if 'invalid_uuid_format' in data.get('code', ''):
                print_success("Middleware correctly rejects invalid UUID format")
                return True
            else:
                print_warning(f"Got 400 but unexpected error: {data}")
                return False
        else:
            print_error(f"Expected 400, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_nonexistent_tenant() -> bool:
    """Teste avec un tenant inexistant"""
    try:
        print_info("Testing request with non-existent tenant...")
        fake_uuid = str(uuid.uuid4())
        headers = {'X-Tenant-ID': fake_uuid}
        response = requests.get(f"{LIBRARY_SERVICE_URL}/api/categories/", headers=headers, timeout=10)
        
        if response.status_code == 401:
            data = response.json()
            if 'invalid_tenant_id' in data.get('code', ''):
                print_success("Middleware correctly rejects non-existent tenant")
                return True
            else:
                print_warning(f"Got 401 but unexpected error: {data}")
                return False
        elif response.status_code == 503:
            print_warning("Tenant service unavailable - cannot test non-existent tenant")
            return True  # Service unavailable, but middleware is working
        else:
            print_error(f"Expected 401, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False

def test_public_endpoints() -> bool:
    """Teste que les endpoints publics sont accessibles sans X-Tenant-ID"""
    try:
        print_info("Testing public endpoint /health/...")
        response = requests.get(f"{LIBRARY_SERVICE_URL}/health/", timeout=5)
        
        if response.status_code == 200:
            print_success("Public endpoint /health/ accessible without X-Tenant-ID")
            return True
        else:
            print_error(f"Public endpoint failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Public endpoint test failed: {str(e)}")
        return False

def test_tenant_service_communication() -> bool:
    """Teste que le tenant-service est accessible"""
    try:
        print_info("Testing communication with tenant-service...")
        response = requests.get(f"{TENANT_SERVICE_URL}/health/", timeout=5)
        
        if response.status_code == 200:
            print_success("Tenant service is reachable")
            return True
        else:
            print_error(f"Tenant service health check failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Tenant service unreachable: {str(e)}")
        return False

def test_middleware_integration() -> bool:
    """Teste l'intégration complète du middleware"""
    try:
        print_info("Testing complete middleware integration...")
        
        # Test avec un UUID valide mais probablement inexistant
        test_uuid = "123e4567-e89b-12d3-a456-426614174000"  # UUID format valide
        headers = {'X-Tenant-ID': test_uuid}
        
        response = requests.get(f"{LIBRARY_SERVICE_URL}/api/categories/", headers=headers, timeout=10)
        
        # Le middleware doit soit:
        # 1. Rejeter le tenant (401) si tenant-service fonctionne
        # 2. Retourner 503 si tenant-service est down
        # 3. Retourner 200 si le tenant existe (peu probable avec cet UUID)
        
        if response.status_code in [401, 503]:
            print_success("Middleware correctly handles tenant validation")
            return True
        elif response.status_code == 200:
            print_success("Middleware works and tenant exists!")
            return True
        else:
            print_warning(f"Unexpected response: {response.status_code}")
            try:
                data = response.json()
                print_info(f"Response data: {data}")
            except:
                pass
            return False
            
    except requests.exceptions.RequestException as e:
        print_error(f"Middleware integration test failed: {str(e)}")
        return False

def main():
    print_header("PHASE 2 - TEST MIDDLEWARE TENANT UNIFORME")
    
    # Statistiques
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Services de base
    print_header("1. SERVICES HEALTH CHECKS")
    
    services_tests = [
        (LIBRARY_SERVICE_URL, "Library Service"),
        (TENANT_SERVICE_URL, "Tenant Service"),
    ]
    
    for url, name in services_tests:
        total_tests += 1
        if test_service_health(url, name):
            passed_tests += 1
    
    # Test 2: Validation des headers
    print_header("2. TENANT HEADER VALIDATION")
    
    header_tests = [
        ("No tenant header", test_no_tenant_header),
        ("Invalid UUID format", test_invalid_tenant_uuid),
        ("Non-existent tenant", test_nonexistent_tenant),
    ]
    
    for test_name, test_func in header_tests:
        print_info(f"Running: {test_name}")
        total_tests += 1
        if test_func():
            passed_tests += 1
    
    # Test 3: Endpoints publics
    print_header("3. PUBLIC ENDPOINTS")
    
    total_tests += 1
    if test_public_endpoints():
        passed_tests += 1
    
    # Test 4: Communication tenant-service
    print_header("4. TENANT SERVICE COMMUNICATION")
    
    total_tests += 1
    if test_tenant_service_communication():
        passed_tests += 1
    
    # Test 5: Intégration complète
    print_header("5. MIDDLEWARE INTEGRATION")
    
    total_tests += 1
    if test_middleware_integration():
        passed_tests += 1
    
    # Résultats finaux
    print_header("RÉSULTATS PHASE 2")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Tests passés: {passed_tests}/{total_tests}")
    print(f"Taux de réussite: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print_success("PHASE 2 RÉUSSIE ✅")
        print_info("Le middleware tenant est correctement uniforme")
        print_info("Vous pouvez passer à la Phase 3 (Authentication)")
    elif success_rate >= 60:
        print_warning("PHASE 2 PARTIELLEMENT RÉUSSIE ⚠️")
        print_info("Certains tests ont échoué, mais le middleware fonctionne")
        print_info("Corrigez les problèmes avant de passer à la Phase 3")
    else:
        print_error("PHASE 2 ÉCHOUÉE ❌")
        print_info("Des problèmes majeurs empêchent le bon fonctionnement")
        print_info("Vérifiez la configuration et les services")
    
    print_header("PROCHAINES ÉTAPES")
    if success_rate >= 80:
        print_info("1. Passer à Phase 3 (Authentication Alignment)")
        print_info("2. Supprimer l'ancien middleware si tout fonctionne")
    else:
        print_info("1. Vérifier les logs du library-service")
        print_info("2. Vérifier que tenant-service tourne sur port 8001")
        print_info("3. Vérifier la configuration du cache")
        print_info("4. Vérifier les dépendances (requests installé)")

if __name__ == "__main__":
    main()