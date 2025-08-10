#!/usr/bin/env python3
"""
Script pour tester l'intégration fournisseur après nettoyage du champ legacy
"""
import os
import django
from django.db import connection

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_service.settings')
django.setup()

from django.contrib.contenttypes.models import ContentType
from library.models import Fourniture
from tenant_schema.models import Client

def test_supplier_integration():
    print("Test de l'integration fournisseur apres suppression du champ legacy\n")
    
    # Lister les tenants disponibles
    print("Tenants disponibles:")
    clients = Client.objects.all()
    for client in clients:
        print(f"  - {client.schema_name} (UUID: {client.tenant_uuid})")
    
    # Tester avec un tenant spécifique
    test_tenant = "94c3319e-5e90-47c2-aa59-7c9ee22846e5"
    print(f"\nTest avec tenant: {test_tenant}")
    
    # Simuler le contexte tenant (changement de schéma)
    schema_name = f"tenant_{test_tenant.replace('-', '_')}"
    print(f"Schema utilise: {schema_name}")
    
    with connection.cursor() as cursor:
        # Changer vers le schéma tenant
        cursor.execute(f"SET search_path TO {schema_name}")
        
        # Vérifier si la table existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = 'library_fourniture'
            );
        """, [schema_name])
        
        table_exists = cursor.fetchone()[0]
        print(f"Table library_fourniture existe: {'OUI' if table_exists else 'NON'}")
        
        if table_exists:
            # Compter les fournitures
            cursor.execute("SELECT COUNT(*) FROM library_fourniture")
            count = cursor.fetchone()[0]
            print(f"Nombre de fournitures: {count}")
            
            # Compter celles avec supplier_id
            cursor.execute("SELECT COUNT(*) FROM library_fourniture WHERE supplier_id IS NOT NULL")
            with_supplier = cursor.fetchone()[0]
            print(f"Fournitures avec supplier_id: {with_supplier}")
            
            if with_supplier > 0:
                # Afficher quelques exemples
                cursor.execute("""
                    SELECT nom, supplier_id 
                    FROM library_fourniture 
                    WHERE supplier_id IS NOT NULL 
                    LIMIT 3
                """)
                examples = cursor.fetchall()
                print("Exemples:")
                for nom, supplier_id in examples:
                    print(f"  - {nom}: {supplier_id}")
                    
                    # Tester l'appel CRM pour ce fournisseur
                    print(f"  Test d'appel CRM pour {supplier_id}...")
                    try:
                        from library.services.supplier_integration import get_supplier_service
                        supplier_service = get_supplier_service(test_tenant)
                        details = supplier_service.get_supplier_details(str(supplier_id))
                        if details:
                            print(f"     SUCCES Détails trouvés: {details.get('nom', 'N/A')}")
                        else:
                            print(f"     ECHEC Aucun détail trouvé")
                    except Exception as e:
                        print(f"     ERREUR: {e}")
        
        # Remettre le schéma par défaut
        cursor.execute("SET search_path TO public")

if __name__ == "__main__":
    test_supplier_integration()