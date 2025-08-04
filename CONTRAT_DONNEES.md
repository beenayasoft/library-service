# Contrats de Données - Service Bibliothèque

## Vue d'ensemble

Ce document définit les contrats de données pour le **service library-service**. Il garantit une intégration cohérente entre le backend et le frontend en spécifiant les structures exactes des données échangées.

**Version**: 1.0  
**Service**: library-service  
**Port**: 8006  
**Base URL**: `/api/v1/` (legacy: `/api/`)  

---

## 📋 Index des Contrats

### Gestion des Catégories (`/categories/`)
- [Categorie](#categorie) - Catégories hiérarchiques

### Gestion des Fournitures (`/fournitures/`)
- [Fourniture](#fourniture) - Matériaux et produits

### Gestion de la Main d'Œuvre (`/main-oeuvre/`)
- [MainOeuvre](#mainoeuvre) - Types de main d'œuvre

### Gestion des Ouvrages (`/ouvrages/`)
- [Ouvrage](#ouvrage) - Ouvrages composés
- [IngredientOuvrage](#ingredientouvrage) - Ingrédients d'ouvrages

### Recherche (`/search/`)
- [LibrarySearch](#librarysearch) - Recherche unifiée

---

## 🏗️ Contrats Gestion des Catégories

### Categorie
**Endpoint**: `GET/POST /api/v1/categories/`

```json
{
  "id": "integer",
  "nom": "string (max: 100)",
  "parent": "integer (foreign key, optional)",
  "position": "integer (min: 0, default: 0)",
  "description": "string (optional)",
  "chemin_complet": "string (readonly)",
  "sous_categories": "array (readonly)",
  "created_at": "datetime (readonly)",
  "updated_at": "datetime (readonly)"
}
```

**Validation**:
- `nom`: Requis, 1-100 caractères
- `position`: Entier positif pour l'ordre d'affichage
- `parent`: Référence vers une autre catégorie (structure hiérarchique)

**Champs calculés**:
- `chemin_complet`: Chemin complet de la catégorie (ex: "Maçonnerie > Murs")
- `sous_categories`: Liste des sous-catégories

---

## 📦 Contrats Gestion des Fournitures

### Fourniture
**Endpoint**: `GET/POST /api/v1/fournitures/`

```json
{
  "id": "integer",
  "nom": "string (max: 100)",
  "unite": "string (max: 20)",
  "prix_achat_ht": "decimal (10,2)",
  "categorie": "integer (foreign key, optional)",
  "categorie_nom": "string (readonly)",
  "description": "string (optional)",
  "reference": "string (max: 50, optional)",
  "supplier": "string (max: 100, optional)",
  "vat_rate": "decimal (5,2, default: 20.0)",
  "type": "string (max: 20, default: 'material')",
  "code": "string (max: 50, optional)",
  "waste_factor": "decimal (5,2, default: 0.0)",
  "is_recyclable": "boolean (default: false)",
  "unitPrice": "decimal (readonly, alias: prix_achat_ht)",
  "vatRate": "decimal (readonly, alias: vat_rate)",
  "wasteFactor": "decimal (readonly, alias: waste_factor)",
  "created_at": "datetime (readonly)",
  "updated_at": "datetime (readonly)"
}
```

**Validation**:
- `nom`: Requis, 1-100 caractères
- `unite`: Requis, unité de mesure (ex: "m", "kg", "pièce")
- `prix_achat_ht`: Requis, prix d'achat HT ≥ 0
- `vat_rate`: Taux de TVA en pourcentage (ex: 20.0 pour 20%)
- `waste_factor`: Facteur de perte en pourcentage

**Relations**:
- `categorie` → Categorie

---

## 👷 Contrats Gestion de la Main d'Œuvre

### MainOeuvre
**Endpoint**: `GET/POST /api/v1/main-oeuvre/`

```json
{
  "id": "integer",
  "nom": "string (max: 100)",
  "cout_horaire": "decimal (10,2)",
  "categorie": "integer (foreign key, optional)",
  "categorie_nom": "string (readonly)",
  "description": "string (optional)",
  "type": "string (max: 20, default: 'labor')",
  "unite": "string (max: 20, default: 'h')",
  "code": "string (max: 50, optional)",
  "skill_level": "APPRENTICE | SKILLED | EXPERT | SPECIALIST (default: SKILLED)",
  "productivity_factor": "decimal (5,2, default: 1.0)",
  "unitPrice": "decimal (readonly, alias: cout_horaire)",
  "prix_achat_ht": "decimal (readonly, alias: cout_horaire)",
  "created_at": "datetime (readonly)",
  "updated_at": "datetime (readonly)"
}
```

**Validation**:
- `nom`: Requis, 1-100 caractères
- `cout_horaire`: Requis, coût horaire ≥ 0
- `skill_level`: Niveau de qualification
- `productivity_factor`: Facteur de productivité (1.0 = normal)

**Relations**:
- `categorie` → Categorie

---

## 🏢 Contrats Gestion des Ouvrages

### Ouvrage
**Endpoint**: `GET/POST /api/v1/ouvrages/`

```json
{
  "id": "integer",
  "nom": "string (max: 200)",
  "unite": "string (max: 20)",
  "categorie": "integer (foreign key, optional)",
  "categorie_nom": "string (readonly)",
  "description": "string (optional)",
  "code": "string (max: 50, optional)",
  "prix_recommande": "decimal (12,2, default: 0)",
  "marge": "decimal (5,2, default: 20.0)",
  "is_custom": "boolean (default: false)",
  "type": "string (max: 20, default: 'work')",
  "complexity": "LOW | MEDIUM | HIGH (default: MEDIUM)",
  "efficiency": "decimal (5,2, default: 1.0)",
  "duration_estimate": "decimal (8,2, optional)",
  "requires_certification": "boolean (default: false)",
  "debourse_sec": "decimal (readonly, calculated)",
  "totalCost": "decimal (readonly, alias: debourse_sec)",
  "recommendedPrice": "decimal (readonly, calculated)",
  "margin": "decimal (readonly, alias: marge)",
  "laborCost": "decimal (readonly, calculated)",
  "materialCost": "decimal (readonly, calculated)",
  "created_at": "datetime (readonly)",
  "updated_at": "datetime (readonly)"
}
```

**Validation**:
- `nom`: Requis, 1-200 caractères
- `unite`: Requis, unité de mesure
- `marge`: Marge en pourcentage (ex: 20.0 pour 20%)
- `efficiency`: Facteur de rendement
- `duration_estimate`: Durée estimée en heures

**Champs calculés**:
- `debourse_sec`: Coût total des ingrédients
- `recommendedPrice`: Prix recommandé avec marge
- `laborCost`: Coût total main d'œuvre
- `materialCost`: Coût total matériaux

**Relations**:
- `categorie` → Categorie

---

### IngredientOuvrage
**Endpoint**: `GET/POST /api/v1/ingredients/`

```json
{
  "id": "integer",
  "ouvrage": "integer (foreign key)",
  "element_type": "integer (foreign key, ContentType)",
  "element_type_nom": "string (write_only: 'fourniture' | 'mainoeuvre')",
  "element_id": "integer",
  "element_nom": "string (readonly)",
  "element_unite": "string (readonly)",
  "element_prix": "decimal (readonly)",
  "quantite": "decimal (10,3)",
  "cout_total": "decimal (readonly, calculated)",
  "waste_allowance": "decimal (5,2, default: 0.0)",
  "notes": "string (optional)",
  "created_at": "datetime (readonly)",
  "updated_at": "datetime (readonly)"
}
```

**Validation**:
- `ouvrage`: Requis, référence vers un ouvrage
- `element_type_nom`: Requis pour création ("fourniture" ou "mainoeuvre")
- `element_id`: Requis, ID de l'élément référencé
- `quantite`: Requis, quantité ≥ 0.001
- `waste_allowance`: Majoration pour pertes en pourcentage

**Contrainte unique**: `(ouvrage, element_type, element_id)`

**Champs calculés**:
- `cout_total`: `quantite * element_prix * (1 + waste_allowance/100)`
- `element_nom`: Nom de l'élément référencé
- `element_unite`: Unité de l'élément référencé
- `element_prix`: Prix unitaire de l'élément référencé

**Relations**:
- `ouvrage` → Ouvrage
- `element_type` + `element_id` → Fourniture ou MainOeuvre (relation générique)

---

## 🔍 Contrats Recherche

### LibrarySearch
**Endpoint**: `GET /api/v1/search/`

```json
{
  "id": "integer",
  "nom": "string",
  "type": "string ('material' | 'labor' | 'work')",
  "unite": "string",
  "unitPrice": "decimal",
  "categorie": "string (optional)",
  "description": "string (optional)",
  "code": "string (optional)",
  "vatRate": "decimal (optional, fournitures)",
  "wasteFactor": "decimal (optional, fournitures)",
  "supplier": "string (optional, fournitures)",
  "skill_level": "string (optional, main d'œuvre)",
  "productivity_factor": "decimal (optional, main d'œuvre)",
  "complexity": "string (optional, ouvrages)",
  "efficiency": "decimal (optional, ouvrages)",
  "duration_estimate": "decimal (optional, ouvrages)",
  "requires_certification": "boolean (optional, ouvrages)"
}
```

**Query Parameters**:
- `search`: Recherche textuelle
- `type`: Filtrer par type ('material', 'labor', 'work')
- `categorie`: Filtrer par catégorie (ID)
- `ordering`: Tri (-created_at, nom, unitPrice, etc.)

---

## 🔗 Relations et Dépendances

### Schéma relationnel
```
Categorie ←--→ Fourniture
    ↓             ↓
    ├─────→ MainOeuvre
    ↓             ↓
    └─────→ Ouvrage ←--→ IngredientOuvrage
                            ↓
                      [Fourniture | MainOeuvre]
```

### Intégrations externes
- **Multi-tenant**: Isolation par schéma PostgreSQL
- **Auth Service**: Gestion des utilisateurs et permissions
- **Document Service**: Intégration pour devis/factures

---

## ⚠️ Règles de Validation

### Format des IDs
Tous les `id` sont des entiers auto-incrémentés

### Contraintes métier
1. **Prix**: Tous les prix doivent être ≥ 0
2. **Quantités**: `quantite` ≥ 0.001
3. **Pourcentages**: `marge`, `vat_rate`, `waste_factor` ≥ 0
4. **Hiérarchie**: Une catégorie ne peut être parent d'elle-même

### États cohérents
- `debourse_sec` calculé automatiquement à partir des ingrédients
- `recommendedPrice` calculé avec marge ou prix fixe
- `cout_total` mis à jour avec waste_allowance

---

## 📝 Exemples d'utilisation

### Créer une fourniture
```http
POST /api/v1/fournitures/
Content-Type: application/json

{
  "nom": "Béton C25/30",
  "unite": "m³",
  "prix_achat_ht": "85.50",
  "categorie": 1,
  "description": "Béton structural",
  "vat_rate": "20.0",
  "waste_factor": "5.0"
}
```

### Créer un ouvrage avec ingrédients
```http
POST /api/v1/ouvrages/
Content-Type: application/json

{
  "nom": "Mur en béton armé",
  "unite": "m²",
  "categorie": 2,
  "description": "Mur porteur en béton armé",
  "marge": "25.0"
}
```

### Ajouter un ingrédient à un ouvrage
```http
POST /api/v1/ingredients/
Content-Type: application/json

{
  "ouvrage": 1,
  "element_type_nom": "fourniture",
  "element_id": 1,
  "quantite": "0.250",
  "waste_allowance": "5.0",
  "notes": "Béton pour structure"
}
```

### Recherche unifiée
```http
GET /api/v1/search/?search=béton&type=material&ordering=unitPrice
```

---

## 🎯 Points d'attention Frontend

### Gestion des états
- Les champs `readonly` ne doivent jamais être envoyés en POST/PUT
- Les alias (`unitPrice`, `totalCost`, etc.) sont pour la compatibilité
- Les `*_display` sont pour l'affichage uniquement

### Format des dates
- **datetime**: ISO 8601 avec timezone (`2025-08-04T10:30:00Z`)

### Pagination
Tous les endpoints de liste supportent la pagination DRF standard :
```json
{
  "count": 150,
  "next": "http://localhost:8006/api/v1/fournitures/?page=2",
  "previous": null,
  "results": [...]
}
```

### Filtres disponibles
Utiliser les query params pour filtrer :
- `?categorie=1`
- `?type=material`
- `?search=terme` (recherche full-text)
- `?ordering=-created_at`

### Relation générique pour IngredientOuvrage
- Utiliser `element_type_nom` en écriture ("fourniture" ou "mainoeuvre")
- Les champs `element_*` sont calculés automatiquement en lecture

---

**Généré automatiquement à partir des modèles Django**  
**Date**: 2025-08-04  
**Équipe Backend**: Service Bibliothèque