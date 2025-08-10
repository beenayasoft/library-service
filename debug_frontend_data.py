#!/usr/bin/env python3
"""
Script pour débugger les données envoyées au frontend
"""
import os
import django
import json
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_service.settings')
django.setup()

from library.models import Fourniture
from library.serializers import FournitureSerializer
from tenant_schema.models import Client

def debug_frontend_data():
    print("=== DEBUG DONNEES FRONTEND ===\n")
    
    # Lister tous les tenants avec leurs données
    print("TENANTS ET LEURS DONNEES:")
    clients = Client.objects.all()
    
    for client in clients:
        tenant_id = str(client.tenant_uuid)
        schema_name = client.schema_name
        print(f"\n--- TENANT: {tenant_id} ({schema_name}) ---")
        
        # Changer vers le schéma du tenant
        with connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema_name}")
            
            # Vérifier les fournitures
            cursor.execute("SELECT COUNT(*) FROM library_fourniture")
            count = cursor.fetchone()[0]
            print(f"Fournitures totales: {count}")
            
            if count > 0:
                cursor.execute("SELECT COUNT(*) FROM library_fourniture WHERE supplier_id IS NOT NULL")
                with_supplier = cursor.fetchone()[0]
                print(f"Avec supplier_id: {with_supplier}")
                
                if with_supplier > 0:
                    # Simuler ce que l'API retourne
                    cursor.execute("""
                        SELECT id, nom, supplier_id 
                        FROM library_fourniture 
                        WHERE supplier_id IS NOT NULL 
                        LIMIT 3
                    """)
                    
                    for row in cursor.fetchall():
                        fourniture_id, nom, supplier_id = row
                        print(f"  - ID {fourniture_id}: {nom}")
                        print(f"    supplier_id: {supplier_id}")
                        
                        # Simuler l'appel du serializer
                        try:
                            # Créer un objet fourniture
                            fourniture = Fourniture.objects.get(id=fourniture_id)
                            
                            # Créer un contexte de requête simulé
                            class MockRequest:
                                def __init__(self, tenant_id):
                                    self.headers = {'X-Tenant-ID': tenant_id}
                            
                            mock_request = MockRequest(tenant_id)
                            
                            # Sérialiser avec contexte
                            serializer = FournitureSerializer(fourniture, context={'request': mock_request})
                            data = serializer.data
                            
                            print(f"    API response:")
                            print(f"      supplier_id: {data.get('supplier_id')}")
                            print(f"      supplier_details: {'OUI' if data.get('supplier_details') else 'NON'}")
                            print(f"      effective_supplier_name: {data.get('effective_supplier_name')}")
                            
                            if data.get('supplier_details'):
                                details = data['supplier_details']
                                print(f"      supplier_details.nom: {details.get('nom', 'N/A')}")
                            
                        except Exception as e:
                            print(f"    ERREUR serialization: {e}")
            
            # Remettre le schéma par défaut
            cursor.execute("SET search_path TO public")
    
    print("\n=== RECOMMENDATIONS ===")
    print("1. Utilisez un tenant qui a des donnees (avec_supplier > 0)")
    print("2. Verifiez que votre frontend utilise le bon tenant ID")
    print("3. Verifiez que l'API retourne supplier_details ou supplier_id")

if __name__ == "__main__":
    debug_frontend_data()