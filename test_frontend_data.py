#!/usr/bin/env python3
"""
Test des données pour le frontend - Service Library
Vérifie que toutes les API fonctionnent avec le tenant de test
"""
import requests

TENANT_ID = "11111111-2222-3333-4444-555555555555"
BASE_URL = "http://localhost:8005"

def test_api_endpoint(endpoint, description):
    """Teste un endpoint de l'API"""
    headers = {
        'X-Tenant-ID': TENANT_ID,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'results' in data:
                count = len(data['results'])
                print(f"  [OK] {description}: {count} éléments")
            elif isinstance(data, list):
                count = len(data)
                print(f"  [OK] {description}: {count} éléments")
            elif isinstance(data, dict):
                print(f"  [OK] {description}: {data}")
            else:
                print(f"  [OK] {description}: réponse OK")
            return True
        else:
            print(f"  [ERROR] {description}: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {description}: {e}")
        return False

def main():
    print("TEST DES DONNEES FRONTEND - SERVICE LIBRARY")
    print("=" * 50)
    print(f"Tenant ID: {TENANT_ID}")
    print(f"Base URL: {BASE_URL}")
    print()
    
    # Tests des endpoints principaux
    tests = [
        ("/health/", "Health Check (sans tenant)"),
        ("/api/categories/", "Liste des catégories"),
        ("/api/categories/racines/", "Catégories racines"),
        ("/api/categories/stats/", "Statistiques catégories"),
        ("/api/fournitures/", "Liste des fournitures"),
        ("/api/fournitures/stats/", "Statistiques fournitures"),
        ("/api/fournitures/par_categorie/", "Fournitures par catégorie"),
        ("/api/main-oeuvre/", "Liste main d'œuvre"),
        ("/api/main-oeuvre/stats/", "Statistiques main d'œuvre"),
        ("/api/main-oeuvre/par_categorie/", "Main d'œuvre par catégorie"),
        ("/api/ouvrages/", "Liste des ouvrages"),
        ("/api/ouvrages/stats/", "Statistiques ouvrages"),
        ("/api/ouvrages/par_categorie/", "Ouvrages par catégorie"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, description in tests:
        if endpoint == "/health/":
            # Health check sans headers
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"  [OK] {description}")
                    passed += 1
                else:
                    print(f"  [ERROR] {description}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  [ERROR] {description}: {e}")
        else:
            if test_api_endpoint(endpoint, description):
                passed += 1
    
    print("\n" + "=" * 50)
    print(f"RESULTATS: {passed}/{total} tests passés")
    
    if passed == total:
        print("\nSUCCES: Toutes les données sont accessibles pour le frontend!")
        print("\nVous pouvez maintenant tester dans l'interface React:")
        print("1. Utilisez le Tenant ID: 11111111-2222-3333-4444-555555555555")
        print("2. Testez les endpoints /api/categories/, /api/fournitures/, etc.")
        print("3. Vérifiez l'intégration avec votre API client")
    else:
        print("\nPROBLEMES: Certains endpoints ne fonctionnent pas")
        print("Vérifiez que le service library est démarré sur le port 8005")

if __name__ == "__main__":
    main()