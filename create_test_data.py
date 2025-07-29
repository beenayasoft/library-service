#!/usr/bin/env python3
"""
Script pour créer des données de test dans le service library
Données réalistes pour le secteur BTP
"""
import os
import sys
import django
import uuid
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_service.settings')
django.setup()

from library.models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage
from tenant_schema.models import Client, Domain
from django.contrib.contenttypes.models import ContentType

def create_test_tenant():
    """Crée un tenant de test"""
    # Utiliser un UUID fixe pour les tests
    test_tenant_uuid = "11111111-2222-3333-4444-555555555555"
    tenant_name = "ETAO Test"
    schema_name = "tenant_etao_test"
    
    try:
        # Vérifier si le tenant existe
        tenant = Client.objects.filter(tenant_uuid=test_tenant_uuid).first()
        if tenant:
            print(f" Tenant de test existant: {tenant.name}")
            return tenant
        
        # Créer le tenant
        tenant = Client.objects.create(
            tenant_uuid=test_tenant_uuid,
            name=tenant_name,
            schema_name=schema_name,
            is_active=True,
            max_library_items=50000
        )
        
        # Créer un domaine pour le tenant
        Domain.objects.get_or_create(
            domain=f"{schema_name}.library.local",
            tenant=tenant,
            defaults={'is_primary': True}
        )
        
        print(f" Tenant de test cree: {tenant.name} (UUID: {test_tenant_uuid})")
        return tenant
        
    except Exception as e:
        print(f" Erreur création tenant: {e}")
        return None

def create_categories(tenant):
    """Crée les categories de test"""
    print("\n Création des categories...")
    
    # Utiliser le schéma du tenant
    from django.db import connection
    connection.set_tenant(tenant)
    
    categories_data = [
        # Catégories principales
        {"nom": "Gros Œuvre", "description": "Fondations, murs, structure", "parent": None, "position": 1},
        {"nom": "Second Œuvre", "description": "Cloisons, finitions", "parent": None, "position": 2},
        {"nom": "Équipements", "description": "Plomberie, électricité, chauffage", "parent": None, "position": 3},
        {"nom": "Finitions", "description": "Peinture, revêtements", "parent": None, "position": 4},
        
        # Sous-categories Gros Œuvre
        {"nom": "Terrassement", "description": "Excavation, remblai", "parent": "Gros Œuvre", "position": 1},
        {"nom": "Fondations", "description": "Semelles, radiers", "parent": "Gros Œuvre", "position": 2},
        {"nom": "Maçonnerie", "description": "Murs, cloisons", "parent": "Gros Œuvre", "position": 3},
        {"nom": "Béton Armé", "description": "Poteaux, poutres, dalles", "parent": "Gros Œuvre", "position": 4},
        
        # Sous-categories Second Œuvre
        {"nom": "Cloisons", "description": "Séparations intérieures", "parent": "Second Œuvre", "position": 1},
        {"nom": "Menuiseries", "description": "Portes, fenêtres", "parent": "Second Œuvre", "position": 2},
        
        # Sous-categories Équipements
        {"nom": "Plomberie", "description": "Canalisations, sanitaires", "parent": "Équipements", "position": 1},
        {"nom": "Électricité", "description": "Câblage, éclairage", "parent": "Équipements", "position": 2},
        {"nom": "Chauffage", "description": "Radiateurs, chaudières", "parent": "Équipements", "position": 3},
        
        # Sous-categories Finitions
        {"nom": "Peinture", "description": "Enduits, peintures", "parent": "Finitions", "position": 1},
        {"nom": "Revêtements Sol", "description": "Carrelage, parquet", "parent": "Finitions", "position": 2},
        {"nom": "Revêtements Mur", "description": "Faïence, papier peint", "parent": "Finitions", "position": 3},
    ]
    
    categories = {}
    created_count = 0
    
    for cat_data in categories_data:
        parent_obj = None
        if cat_data["parent"]:
            parent_obj = categories.get(cat_data["parent"])
        
        category, created = Categorie.objects.get_or_create(
            nom=cat_data["nom"],
            defaults={
                'description': cat_data["description"],
                'parent': parent_obj,
                'position': cat_data["position"]
            }
        )
        
        categories[cat_data["nom"]] = category
        if created:
            created_count += 1
            print(f"  [OK] {category.nom}")
    
    print(f" {created_count} categories crees")
    return categories

def create_fournitures(categories):
    """Crée les fournitures de test"""
    print("\n Création des fournitures...")
    
    fournitures_data = [
        # Maçonnerie
        {"nom": "Brique creuse 20cm", "categorie": "Maçonnerie", "unite": "m²", "prix": 35.50, "reference": "BRQ-20", "type": "standard"},
        {"nom": "Parpaing 20x20x50", "categorie": "Maçonnerie", "unite": "u", "prix": 2.15, "reference": "PAR-20", "type": "standard"},
        {"nom": "Mortier colle", "categorie": "Maçonnerie", "unite": "sac", "prix": 8.90, "reference": "MOR-COL", "type": "standard"},
        {"nom": "Linteau béton 1.5m", "categorie": "Maçonnerie", "unite": "u", "prix": 28.00, "reference": "LIN-150", "type": "préfabriqué"},
        
        # Béton Armé
        {"nom": "Béton C25/30", "categorie": "Béton Armé", "unite": "m³", "prix": 95.00, "reference": "BET-C25", "type": "standard"},
        {"nom": "Acier HA 10", "categorie": "Béton Armé", "unite": "kg", "prix": 1.20, "reference": "AC-HA10", "type": "standard"},
        {"nom": "Acier HA 12", "categorie": "Béton Armé", "unite": "kg", "prix": 1.25, "reference": "AC-HA12", "type": "standard"},
        {"nom": "Treillis soudé", "categorie": "Béton Armé", "unite": "m²", "prix": 8.50, "reference": "TRE-SOU", "type": "standard"},
        
        # Plomberie
        {"nom": "Tube PVC Ø100", "categorie": "Plomberie", "unite": "ml", "prix": 4.20, "reference": "TUB-100", "type": "standard"},
        {"nom": "Tube PVC Ø50", "categorie": "Plomberie", "unite": "ml", "prix": 2.80, "reference": "TUB-50", "type": "standard"},
        {"nom": "Coude PVC 90° Ø100", "categorie": "Plomberie", "unite": "u", "prix": 3.50, "reference": "COU-100", "type": "standard"},
        {"nom": "WC suspendu", "categorie": "Plomberie", "unite": "u", "prix": 185.00, "reference": "WC-SUS", "type": "équipement"},
        {"nom": "Lavabo 60cm", "categorie": "Plomberie", "unite": "u", "prix": 120.00, "reference": "LAV-60", "type": "équipement"},
        
        # Électricité
        {"nom": "Cable H07V-U 2.5mm²", "categorie": "Électricité", "unite": "ml", "prix": 0.85, "reference": "CAB-25", "type": "standard"},
        {"nom": "Cable H07V-U 1.5mm²", "categorie": "Électricité", "unite": "ml", "prix": 0.65, "reference": "CAB-15", "type": "standard"},
        {"nom": "Disjoncteur 20A", "categorie": "Électricité", "unite": "u", "prix": 12.50, "reference": "DIS-20A", "type": "protection"},
        {"nom": "Prise 2P+T", "categorie": "Électricité", "unite": "u", "prix": 4.20, "reference": "PRI-2PT", "type": "appareillage"},
        
        # Peinture
        {"nom": "Peinture acrylique blanc", "categorie": "Peinture", "unite": "L", "prix": 12.50, "reference": "PEIN-ACR", "type": "finition"},
        {"nom": "Sous-couche universelle", "categorie": "Peinture", "unite": "L", "prix": 8.90, "reference": "SOUS-COU", "type": "préparation"},
        {"nom": "Enduit de lissage", "categorie": "Peinture", "unite": "kg", "prix": 1.85, "reference": "END-LIS", "type": "préparation"},
        
        # Menuiseries
        {"nom": "Porte intérieure 83cm", "categorie": "Menuiseries", "unite": "u", "prix": 145.00, "reference": "POR-83", "type": "menuiserie"},
        {"nom": "Fenêtre PVC 100x120", "categorie": "Menuiseries", "unite": "u", "prix": 285.00, "reference": "FEN-100", "type": "menuiserie"},
        
        # Revêtements
        {"nom": "Carrelage 30x30 grès", "categorie": "Revêtements Sol", "unite": "m²", "prix": 18.50, "reference": "CAR-30", "type": "revêtement"},
        {"nom": "Parquet stratifié", "categorie": "Revêtements Sol", "unite": "m²", "prix": 22.00, "reference": "PAR-STR", "type": "revêtement"},
        {"nom": "Faïence 20x25 blanc", "categorie": "Revêtements Mur", "unite": "m²", "prix": 15.80, "reference": "FAI-20", "type": "revêtement"},
    ]
    
    created_count = 0
    
    for four_data in fournitures_data:
        categorie = categories.get(four_data["categorie"])
        if not categorie:
            print(f"   Catégorie non trouvée: {four_data['categorie']}")
            continue
        
        fourniture, created = Fourniture.objects.get_or_create(
            nom=four_data["nom"],
            defaults={
                'categorie': categorie,
                'unite': four_data["unite"],
                'prix_achat_ht': Decimal(str(four_data["prix"])),
                'reference': four_data["reference"],
                'type': four_data["type"],
                'description': f"Fourniture {four_data['nom']} - {four_data['type']}",
                'is_recyclable': four_data["type"] in ["standard", "préfabriqué"]
            }
        )
        
        if created:
            created_count += 1
            print(f"   {fourniture.nom} - {fourniture.prix_achat_ht}€/{fourniture.unite}")
    
    print(f" {created_count} fournitures crees")

def create_main_oeuvre(categories):
    """Crée la main d'oeuvre de test"""
    print("\n Création de la main d'oeuvre...")
    
    main_oeuvre_data = [
        # Gros Œuvre
        {"nom": "Maçon", "categorie": "Maçonnerie", "cout": 35.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        {"nom": "Aide maçon", "categorie": "Maçonnerie", "cout": 22.00, "unite": "h", "skill": "novice", "type": "ouvrier"},
        {"nom": "Chef d'équipe maçonnerie", "categorie": "Maçonnerie", "cout": 42.00, "unite": "h", "skill": "expert", "type": "encadrement"},
        {"nom": "Coffreur", "categorie": "Béton Armé", "cout": 38.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        {"nom": "Ferrailleur", "categorie": "Béton Armé", "cout": 36.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        
        # Second Œuvre
        {"nom": "Plaquiste", "categorie": "Cloisons", "cout": 32.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        {"nom": "Menuisier", "categorie": "Menuiseries", "cout": 40.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        
        # Équipements
        {"nom": "Plombier", "categorie": "Plomberie", "cout": 45.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        {"nom": "Électricien", "categorie": "Électricité", "cout": 48.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        {"nom": "Chauffagiste", "categorie": "Chauffage", "cout": 50.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        
        # Finitions
        {"nom": "Peintre", "categorie": "Peinture", "cout": 28.00, "unite": "h", "skill": "intermediaire", "type": "ouvrier"},
        {"nom": "Carreleur", "categorie": "Revêtements Sol", "cout": 35.00, "unite": "h", "skill": "expert", "type": "ouvrier"},
        
        # Terrassement
        {"nom": "Conducteur d'engin", "categorie": "Terrassement", "cout": 38.00, "unite": "h", "skill": "expert", "type": "conducteur"},
        {"nom": "Terrassier", "categorie": "Terrassement", "cout": 25.00, "unite": "h", "skill": "intermediaire", "type": "ouvrier"},
        
        # Encadrement
        {"nom": "Chef de chantier", "categorie": "Gros Œuvre", "cout": 55.00, "unite": "h", "skill": "expert", "type": "encadrement"},
        {"nom": "Contremaître", "categorie": "Second Œuvre", "cout": 48.00, "unite": "h", "skill": "expert", "type": "encadrement"},
    ]
    
    created_count = 0
    
    for mo_data in main_oeuvre_data:
        categorie = categories.get(mo_data["categorie"])
        if not categorie:
            print(f"   Catégorie non trouvée: {mo_data['categorie']}")
            continue
        
        main_oeuvre, created = MainOeuvre.objects.get_or_create(
            nom=mo_data["nom"],
            defaults={
                'categorie': categorie,
                'cout_horaire': Decimal(str(mo_data["cout"])),
                'unite': mo_data["unite"],
                'skill_level': mo_data["skill"],
                'type': mo_data["type"],
                'description': f"Main d'oeuvre {mo_data['nom']} - {mo_data['skill']}",
                'code': mo_data["nom"].upper().replace(" ", "_")
            }
        )
        
        if created:
            created_count += 1
            print(f"   {main_oeuvre.nom} - {main_oeuvre.cout_horaire}€/{main_oeuvre.unite}")
    
    print(f" {created_count} types de main d'oeuvre crees")

def create_ouvrages(categories):
    """Crée les ouvrages de test"""
    print("\n Création des ouvrages...")
    
    ouvrages_data = [
        # Gros Œuvre
        {"nom": "Mur parpaing 20cm", "categorie": "Maçonnerie", "unite": "m²", "prix": 45.00, "complexity": "simple"},
        {"nom": "Cloison brique 10cm", "categorie": "Maçonnerie", "unite": "m²", "prix": 38.00, "complexity": "simple"},
        {"nom": "Dalle béton 20cm", "categorie": "Béton Armé", "unite": "m²", "prix": 85.00, "complexity": "intermediate"},
        {"nom": "Poteau béton armé", "categorie": "Béton Armé", "unite": "u", "prix": 180.00, "complexity": "complex"},
        {"nom": "Fondation semelle 60cm", "categorie": "Fondations", "unite": "ml", "prix": 95.00, "complexity": "intermediate"},
        
        # Second Œuvre
        {"nom": "Cloison placo 70mm", "categorie": "Cloisons", "unite": "m²", "prix": 28.00, "complexity": "simple"},
        {"nom": "Pose porte intérieure", "categorie": "Menuiseries", "unite": "u", "prix": 185.00, "complexity": "intermediate"},
        {"nom": "Pose fenêtre PVC", "categorie": "Menuiseries", "unite": "u", "prix": 320.00, "complexity": "intermediate"},
        
        # Équipements
        {"nom": "Installation WC complet", "categorie": "Plomberie", "unite": "u", "prix": 285.00, "complexity": "intermediate"},
        {"nom": "Réseau évacuation", "categorie": "Plomberie", "unite": "ml", "prix": 25.00, "complexity": "simple"},
        {"nom": "Tableau électrique 3 rangées", "categorie": "Électricité", "unite": "u", "prix": 450.00, "complexity": "complex"},
        {"nom": "Point lumineux", "categorie": "Électricité", "unite": "u", "prix": 85.00, "complexity": "simple"},
        {"nom": "Prise électrique 2P+T", "categorie": "Électricité", "unite": "u", "prix": 45.00, "complexity": "simple"},
        
        # Finitions
        {"nom": "Peinture mur 2 couches", "categorie": "Peinture", "unite": "m²", "prix": 18.50, "complexity": "simple"},
        {"nom": "Pose carrelage sol", "categorie": "Revêtements Sol", "unite": "m²", "prix": 42.00, "complexity": "intermediate"},
        {"nom": "Pose parquet flottant", "categorie": "Revêtements Sol", "unite": "m²", "prix": 35.00, "complexity": "intermediate"},
        {"nom": "Pose faïence murale", "categorie": "Revêtements Mur", "unite": "m²", "prix": 38.00, "complexity": "intermediate"},
        
        # Terrassement
        {"nom": "Excavation terrain", "categorie": "Terrassement", "unite": "m³", "prix": 12.00, "complexity": "simple"},
        {"nom": "Remblai compacté", "categorie": "Terrassement", "unite": "m³", "prix": 15.00, "complexity": "simple"},
    ]
    
    created_count = 0
    ouvrages_created = []
    
    for ouv_data in ouvrages_data:
        categorie = categories.get(ouv_data["categorie"])
        if not categorie:
            print(f"   Catégorie non trouvée: {ouv_data['categorie']}")
            continue
        
        ouvrage, created = Ouvrage.objects.get_or_create(
            nom=ouv_data["nom"],
            defaults={
                'categorie': categorie,
                'unite': ouv_data["unite"],
                'prix_recommande': Decimal(str(ouv_data["prix"])),
                'complexity': ouv_data["complexity"],
                'type': 'standard',
                'description': f"Ouvrage {ouv_data['nom']} - {ouv_data['complexity']}",
                'code': ouv_data["nom"].upper().replace(" ", "_")[:20],
                'is_custom': False,
                'requires_certification': ouv_data["complexity"] == "complex"
            }
        )
        
        if created:
            created_count += 1
            ouvrages_created.append(ouvrage)
            print(f"   {ouvrage.nom} - {ouvrage.prix_recommande}€/{ouvrage.unite}")
    
    print(f" {created_count} ouvrages crees")
    return ouvrages_created

def main():
    """Fonction principale"""
    print("CREATION DES DONNEES DE TEST - SERVICE LIBRARY")
    print("=" * 60)
    
    # Créer le tenant de test
    tenant = create_test_tenant()
    if not tenant:
        return
    
    # Utiliser le schéma du tenant
    from django.db import connection
    connection.set_tenant(tenant)
    
    try:
        # Créer les données dans l'ordre
        categories = create_categories(tenant)
        create_fournitures(categories)
        create_main_oeuvre(categories)
        ouvrages = create_ouvrages(categories)
        
        print("\n" + "=" * 60)
        print("DONNEES DE TEST CREEES AVEC SUCCES")
        print("Statistiques:")
        print(f"   - Tenant: {tenant.name} (UUID: {tenant.tenant_uuid})")
        print(f"   - Categories: {Categorie.objects.count()}")
        print(f"   - Fournitures: {Fourniture.objects.count()}")
        print(f"   - Main d'oeuvre: {MainOeuvre.objects.count()}")
        print(f"   - Ouvrages: {Ouvrage.objects.count()}")
        
        print("\nINFORMATIONS POUR LE FRONTEND:")
        print(f"   - Tenant ID: {tenant.tenant_uuid}")
        print(f"   - Schema: {tenant.schema_name}")
        print(f"   - Service URL: http://localhost:8005")
        print(f"   - API Gateway: http://localhost:8000")
        
        print("\nENDPOINTS A TESTER:")
        print("   - GET /api/categories/")
        print("   - GET /api/fournitures/")
        print("   - GET /api/main-oeuvre/")
        print("   - GET /api/ouvrages/")
        print("   - GET /api/categories/stats/")
        print("   - GET /api/fournitures/par_categorie/")
        
    except Exception as e:
        print(f"ERREUR lors de la creation des donnees: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Remettre le schéma public
        connection.set_schema_to_public()

if __name__ == "__main__":
    main()