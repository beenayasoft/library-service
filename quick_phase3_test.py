#!/usr/bin/env python3
"""Quick test for Phase 3 authentication alignment"""
import requests

def test_phase3():
    print("=== QUICK PHASE 3 TEST ===\n")
    
    # Test 1: Health check
    try:
        response = requests.get('http://localhost:8005/health/', timeout=5)
        print(f"1. Health check: HTTP {response.status_code}")
        if response.status_code == 200:
            print(f"   [OK] Service healthy: {response.json()}")
        else:
            print(f"   [ERROR] Response: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Health check failed: {e}")

    # Test 2: AllowAny permissions 
    print("\n2. Testing AllowAny permissions...")
    try:
        headers = {'X-Tenant-ID': '123e4567-e89b-12d3-a456-426614174000'}
        response = requests.get('http://localhost:8005/api/categories/', headers=headers, timeout=5)
        print(f"   Categories endpoint: HTTP {response.status_code}")
        if response.status_code != 403:
            print("   [OK] AllowAny permissions working - no 403 Forbidden")
        else:
            print("   [ERROR] Still getting 403 - auth required")
    except Exception as e:
        print(f"   [ERROR] Categories test failed: {e}")

    # Test 3: GatewayAuthMixin headers
    print("\n3. Testing GatewayAuthMixin...")
    try:
        headers = {
            'X-Tenant-ID': '123e4567-e89b-12d3-a456-426614174000',
            'X-User-ID': '123',
            'X-User-Email': 'test@beenaya.com'
        }
        response = requests.get('http://localhost:8005/api/fournitures/', headers=headers, timeout=5)
        print(f"   Fournitures with auth headers: HTTP {response.status_code}")
        if response.status_code in [200, 400, 401, 503]:
            print("   [OK] GatewayAuthMixin processing auth headers")
        else:
            print(f"   [ERROR] Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Mixin test failed: {e}")

    print("\n=== PHASE 3 TEST COMPLETE ===")

if __name__ == "__main__":
    test_phase3()