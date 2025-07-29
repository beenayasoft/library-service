#!/usr/bin/env python3
"""
Test pour valider l'optimisation du middleware contre les race conditions
"""
import requests
import threading
import time

def test_concurrent_requests():
    """Simule plusieurs requêtes simultanées pour tester les race conditions"""
    print("=== TEST CONCURRENCE MIDDLEWARE ===\n")
    
    def make_request(thread_id):
        try:
            headers = {
                'X-Tenant-ID': '31f96c39-bd7f-453e-a7f1-88495e70272b',
                'X-User-ID': f'user_{thread_id}',
                'X-User-Email': f'user{thread_id}@test.com'
            }
            response = requests.get('http://localhost:8005/api/categories/', headers=headers, timeout=5)
            print(f"Thread {thread_id}: HTTP {response.status_code}")
            return response.status_code
        except Exception as e:
            print(f"Thread {thread_id}: ERROR {e}")
            return 500
    
    # Lancer 5 requêtes simultanées
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request, args=(i,))
        threads.append(thread)
    
    print("Lancement de 5 requêtes simultanées...")
    start_time = time.time()
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"\nTemps total: {end_time - start_time:.2f}s")
    print("Test de concurrence terminé")

if __name__ == "__main__":
    test_concurrent_requests()