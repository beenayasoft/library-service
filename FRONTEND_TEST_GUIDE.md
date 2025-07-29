# Guide de Test Frontend - Service Library

## 🎯 Données de Test Créées

### Tenant de Test
- **Tenant ID**: `11111111-2222-3333-4444-555555555555`
- **Nom**: ETAO Test
- **Schema**: tenant_etao_test

### Statistiques des Données
- **16 Catégories** (hiérarchie Gros Œuvre > Maçonnerie, etc.)
- **25 Fournitures** (briques, parpaings, tubes, câbles, etc.)
- **16 Types Main d'Œuvre** (maçon, plombier, électricien, etc.)
- **19 Ouvrages** (murs, dalles, installations, etc.)

## 🌐 URLs de Test

### Service Direct (Debug)
- **Base URL**: `http://localhost:8005`
- **Health Check**: `http://localhost:8005/health/`

### Via API Gateway (Production)
- **Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health/`

## 📡 Headers Requis

### Headers Obligatoires
```javascript
{
  'X-Tenant-ID': '11111111-2222-3333-4444-555555555555',
  'Content-Type': 'application/json'
}
```

### Headers Optionnels (Simulation Authentification)
```javascript
{
  'X-User-ID': '123',
  'X-User-Email': 'test@beenaya.com',
  'Authorization': 'Bearer fake-jwt-token'
}
```

## 🔗 Endpoints à Tester

### 1. Catégories
```javascript
// Liste des catégories
GET /api/categories/
// Réponse: Array de catégories avec parent/enfants

// Catégories racines seulement
GET /api/categories/racines/
// Réponse: Gros Œuvre, Second Œuvre, Équipements, Finitions

// Statistiques catégories
GET /api/categories/stats/
// Réponse: { total_categories: 16, categories_racines: 4, ... }

// Sous-catégories d'une catégorie
GET /api/categories/{id}/sous_categories/
// Exemple: /api/categories/1/sous_categories/
```

### 2. Fournitures
```javascript
// Liste des fournitures
GET /api/fournitures/
// Réponse: Array de fournitures avec prix, unités, références

// Fournitures par catégorie
GET /api/fournitures/par_categorie/
// Réponse: { "Maçonnerie": [...], "Plomberie": [...] }

// Statistiques fournitures
GET /api/fournitures/stats/
// Réponse: { total: 25, prix_moyen: 45.67, ... }

// Filtres disponibles
GET /api/fournitures/?categorie=1
GET /api/fournitures/?type=standard
GET /api/fournitures/?search=brique
```

### 3. Main d'Œuvre
```javascript
// Liste main d'œuvre
GET /api/main-oeuvre/
// Réponse: Array avec coûts horaires, niveaux de compétence

// Par catégorie
GET /api/main-oeuvre/par_categorie/
// Réponse: { "Maçonnerie": [...], "Plomberie": [...] }

// Statistiques
GET /api/main-oeuvre/stats/
// Réponse: { total: 16, cout_moyen: 38.5, ... }

// Filtres
GET /api/main-oeuvre/?skill_level=expert
GET /api/main-oeuvre/?type=ouvrier
```

### 4. Ouvrages
```javascript
// Liste des ouvrages
GET /api/ouvrages/
// Réponse: Array avec prix recommandés, complexité

// Par catégorie
GET /api/ouvrages/par_categorie/
// Réponse: { "Maçonnerie": [...], "Béton Armé": [...] }

// Statistiques
GET /api/ouvrages/stats/
// Réponse: { total: 19, prix_moyen: 87.5, ... }

// Filtres
GET /api/ouvrages/?complexity=simple
GET /api/ouvrages/?requires_certification=true
```

### 5. Recherche Globale
```javascript
// Recherche dans toute la bibliothèque
GET /api/library/search/search/?q=beton
// Réponse: { categories: [...], fournitures: [...], ouvrages: [...] }
```

## 🧪 Tests à Effectuer

### Test 1: Connexion Basique
```javascript
// Vérifier que le service répond
fetch('http://localhost:8005/health/', {
  method: 'GET'
})
.then(response => response.json())
.then(data => console.log('Service health:', data));
```

### Test 2: Liste des Catégories
```javascript
// Récupérer les catégories avec headers
fetch('http://localhost:8005/api/categories/', {
  headers: {
    'X-Tenant-ID': '11111111-2222-3333-4444-555555555555',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(categories => {
  console.log('Categories:', categories);
  console.log('Nombre de catégories:', categories.length);
});
```

### Test 3: Fournitures avec Filtres
```javascript
// Test filtrage par catégorie
fetch('http://localhost:8005/api/fournitures/?categorie=3', {
  headers: {
    'X-Tenant-ID': '11111111-2222-3333-4444-555555555555'
  }
})
.then(response => response.json())
.then(fournitures => {
  console.log('Fournitures Maçonnerie:', fournitures.results);
});
```

### Test 4: Recherche
```javascript
// Test recherche globale
fetch('http://localhost:8005/api/library/search/search/?q=macon', {
  headers: {
    'X-Tenant-ID': '11111111-2222-3333-4444-555555555555'
  }
})
.then(response => response.json())
.then(results => {
  console.log('Résultats recherche:', results);
  console.log('Total:', results.total_results);
});
```

## 🔧 Tests d'Intégration Frontend

### Dans votre composant React
```tsx
// Example: beena/src/components/library/LibraryTest.tsx
import { useEffect, useState } from 'react';
import { api } from '@/lib/api/client';

export function LibraryTest() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // L'API client devrait automatiquement ajouter les headers
        const response = await api.get('/api/categories/');
        setCategories(response.data);
      } catch (error) {
        console.error('Erreur:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h2>Test Service Library</h2>
      <p>Catégories trouvées: {categories.length}</p>
      <ul>
        {categories.map(cat => (
          <li key={cat.id}>{cat.nom} - {cat.description}</li>
        ))}
      </ul>
    </div>
  );
}
```

## 📊 Données d'Exemple Attendues

### Catégorie
```json
{
  "id": 1,
  "nom": "Gros Œuvre",
  "description": "Fondations, murs, structure",
  "parent": null,
  "position": 1,
  "chemin_complet": "Gros Œuvre",
  "sous_categories": [
    {
      "id": 5,
      "nom": "Terrassement",
      "parent": 1
    }
  ]
}
```

### Fourniture
```json
{
  "id": 1,
  "nom": "Brique creuse 20cm",
  "categorie": {
    "id": 7,
    "nom": "Maçonnerie"
  },
  "unite": "m²",
  "prix_achat_ht": "35.50",
  "reference": "BRQ-20",
  "type": "standard",
  "is_recyclable": true
}
```

### Main d'Œuvre
```json
{
  "id": 1,
  "nom": "Maçon",
  "categorie": {
    "id": 7,
    "nom": "Maçonnerie"
  },
  "cout_horaire": "35.00",
  "unite": "h",
  "skill_level": "expert",
  "type": "ouvrier"
}
```

### Ouvrage
```json
{
  "id": 1,
  "nom": "Mur parpaing 20cm",
  "categorie": {
    "id": 7,
    "nom": "Maçonnerie"
  },
  "unite": "m²",
  "prix_recommande": "45.00",
  "complexity": "simple",
  "requires_certification": false
}
```

## ⚠️ Points d'Attention

### Erreurs Attendues
- **HTTP 400**: Header X-Tenant-ID manquant
- **HTTP 401**: Tenant ID invalide
- **HTTP 503**: Tenant-service indisponible

### Cas de Test Négatifs
```javascript
// Test sans header (doit échouer)
fetch('http://localhost:8005/api/categories/')
// Attendu: HTTP 400

// Test avec mauvais tenant ID
fetch('http://localhost:8005/api/categories/', {
  headers: { 'X-Tenant-ID': 'invalid-uuid' }
})
// Attendu: HTTP 400
```

## 🚀 Prochaines Étapes

1. **Intégrer dans l'interface Beenaya**
2. **Créer les composants de bibliothèque**
3. **Tester la création de devis avec éléments library**
4. **Valider les performances avec plus de données**

---

**Note**: Assurez-vous que le service library (port 8005) et l'API Gateway (port 8000) sont démarrés avant les tests.