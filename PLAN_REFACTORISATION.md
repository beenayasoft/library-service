# 🚀 Plan de Refactorisation - Service Library

*Document de planification pour l'intégration complète du service library dans l'architecture SOA*

## 🎯 Objectifs de la Refactorisation

### Objectifs Principaux
1. **Intégrer le service library dans l'API Gateway**
2. **Uniformiser l'architecture multi-tenant**
3. **Aligner les patterns d'authentification**
4. **Permettre la communication frontend-backend**
5. **Assurer la cohérence avec les autres services**

### Critères de Succès
- ✅ Service accessible via l'API Gateway
- ✅ Frontend peut consommer les API library
- ✅ Isolation tenant fonctionnelle et cohérente
- ✅ Tests d'intégration passants
- ✅ Documentation à jour

## 📋 Plan d'Action par Phases

### 🔴 **Phase 1: Intégration API Gateway** (Priorité Critique)
*Durée estimée: 1 jour*

#### Tâches détaillées:

**1.1 Configurer le service dans l'API Gateway**
```bash
# Fichier: soa/api-gateway/config.py
```
- [ ] Ajouter "library" dans SERVICES avec port 8005
- [ ] Définir les routes principales: `/api/library/`
- [ ] Configurer le health check: `/health/`

**1.2 Mapper les routes legacy**
- [ ] `/api/categories/` → `("library", "/api/categories/")`
- [ ] `/api/fournitures/` → `("library", "/api/fournitures/")`  
- [ ] `/api/main-oeuvre/` → `("library", "/api/main-oeuvre/")`
- [ ] `/api/ouvrages/` → `("library", "/api/ouvrages/")`
- [ ] `/api/ingredients/` → `("library", "/api/ingredients/")`
- [ ] `/api/library/search/` → `("library", "/api/search/")`

**1.3 Tester le routage**
- [ ] Démarrer library-service sur port 8005
- [ ] Tester health check via Gateway
- [ ] Valider le proxy des requêtes

**Livrables Phase 1:**
- Configuration API Gateway mise à jour
- Service library accessible via Gateway
- Tests de routage validés

---

### 🟡 **Phase 2: Uniformisation du Middleware Tenant** (Priorité Haute)
*Durée estimée: 2 jours*

#### Problèmes actuels identifiés:
- Middleware custom non aligné avec CRM/Document
- Création automatique de tenants (risque de sécurité)
- Logique de validation UUID trop stricte

#### Tâches détaillées:

**2.1 Remplacer le middleware existant**
```python
# Fichier: library/middleware_hybrid.py → SUPPRIMER
# Fichier: library_service/settings.py → MODIFIER
```
- [ ] Copier le middleware de `crm-service/tenant_metier/middleware.py`
- [ ] Adapter pour le service library
- [ ] Supprimer la logique de création automatique
- [ ] Implémenter la communication avec tenant-service

**2.2 Modifier les settings.py**
```python
# Remplacer:
'library.middleware_hybrid.HeaderTenantMiddleware'
# Par:
'library.middleware.HeaderTenantMiddleware'
```

**2.3 Tester l'isolation tenant**
- [ ] Créer 2 tenants de test
- [ ] Valider l'isolation des données
- [ ] Tester le switching de schémas

**Livrables Phase 2:**
- Middleware uniforme implémenté
- Communication tenant-service fonctionnelle
- Tests d'isolation validés

---

### 🟢 **Phase 3: Alignment Authentication** (Priorité Moyenne)
*Durée estimée: 1 jour*

#### Tâches détaillées:

**3.1 Modifier REST Framework settings**
```python
# Fichier: library_service/settings.py
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Changement critique
    ],
    # Supprimer DEFAULT_AUTHENTICATION_CLASSES
}
```

**3.2 Laisser l'API Gateway gérer l'auth**
- [ ] Supprimer les dépendances JWT directes
- [ ] Utiliser les headers X-User-ID, X-Tenant-ID propagés
- [ ] Tester l'authentification via Gateway

**3.3 Nettoyer les dépendances**
```python
# requirements.txt - SUPPRIMER:
# djangorestframework-simplejwt
```

**Livrables Phase 3:**
- Authentication déléguée à l'API Gateway
- Permissions alignées avec les autres services
- Tests d'authentification passants

---

### 🔵 **Phase 4: Simplification du Modèle Tenant** (Priorité Basse)
*Durée estimée: 1 jour*

#### Tâches détaillées:

**4.1 Simplifier le modèle Client** 
```python
# Fichier: tenant_schema/models.py
class Client(TenantMixin):
    name = models.CharField(max_length=100)
    tenant_uuid = models.UUIDField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # SUPPRIMER: company_type, contact_email, etc.
```

**4.2 Créer et appliquer la migration**
- [ ] `python manage.py makemigrations`
- [ ] Tester la migration en dry-run
- [ ] Appliquer avec sauvegarde préalable

**4.3 Nettoyer le modèle Domain**
- [ ] Garder seulement les champs essentiels
- [ ] Supprimer is_https_only, description

**Livrables Phase 4:**
- Modèles tenant uniformisés
- Migrations appliquées sans perte de données
- Structure cohérente avec CRM/Document

---

### 🟣 **Phase 5: Tests et Validation** (Priorité Haute)
*Durée estimée: 2 jours*

#### Tâches détaillées:

**5.1 Tests Backend-to-Backend**
- [ ] Health check via API Gateway
- [ ] CRUD operations pour chaque entité
- [ ] Tests multi-tenant (isolation)
- [ ] Tests de performance basiques

**5.2 Tests Frontend-Backend**
- [ ] Intégration avec l'interface existante
- [ ] Tests des appels API via client.ts
- [ ] Validation des transformations de données
- [ ] Tests des modales et formulaires

**5.3 Tests d'Intégration**
- [ ] Service library + tenant-service
- [ ] Service library + document-service (pour devis)
- [ ] Workflow complet: création ouvrage → ajout au devis

**5.4 Tests de Régression**
- [ ] Vérifier que les autres services fonctionnent toujours
- [ ] Tests des routes existantes
- [ ] Validation des performances Gateway

**Livrables Phase 5:**
- Suite de tests complète
- Documentation des API
- Rapport de validation
- Service prêt pour production

---

## ⚠️ Risques et Mitigation

### Risques Techniques

**🔴 Risque Élevé: Corruption de données tenant**
- **Impact**: Perte de données ou mélange entre tenants
- **Mitigation**: 
  - Sauvegardes avant chaque phase
  - Tests d'isolation rigoureux
  - Validation sur environnement de staging

**🟡 Risque Moyen: Régression sur autres services**
- **Impact**: CRM/Document services affectés
- **Mitigation**:
  - Tests de régression systématiques
  - Déploiement par phases
  - Rollback plan préparé

**🟢 Risque Faible: Performance API Gateway**
- **Impact**: Latence accrue
- **Mitigation**:
  - Tests de charge
  - Monitoring des temps de réponse
  - Configuration cache si nécessaire

### Risques Fonctionnels

**🔴 Risque Élevé: Frontend cassé**
- **Impact**: Interface library inutilisable
- **Mitigation**:
  - Tests frontend systématiques
  - Validation avec données réelles
  - Environnement de test dédié

**🟡 Risque Moyen: Migration données**
- **Impact**: Perte de données existantes
- **Mitigation**:
  - Backup complet avant migration
  - Script de rollback préparé
  - Validation post-migration

## 📅 Planning et Dépendances

### Chronologie Recommandée
```
Jour 1: Phase 1 (API Gateway)
Jour 2-3: Phase 2 (Middleware Tenant) 
Jour 4: Phase 3 (Authentication)
Jour 5: Phase 4 (Modèle Tenant)
Jour 6-7: Phase 5 (Tests & Validation)
```

### Dépendances Critiques
- **Phase 2 dépend de Phase 1**: Service doit être accessible
- **Phase 3 peut être parallèle à Phase 2**: Pas de conflit
- **Phase 5 dépend de toutes les autres**: Tests d'intégration

### Points de Validation
- **Fin Phase 1**: Gateway route vers library-service
- **Fin Phase 2**: Isolation tenant validée  
- **Fin Phase 3**: Auth via Gateway fonctionnelle
- **Fin Phase 4**: Modèles uniformisés
- **Fin Phase 5**: Service production-ready

## 🛠️ Environnement et Outils

### Prérequis Techniques
- [ ] Environnement de développement fonctionnel
- [ ] Base de données PostgreSQL avec schémas tenant
- [ ] API Gateway démarré sur port 8000  
- [ ] Services CRM/Document/Tenant opérationnels
- [ ] Frontend Vite sur port 8080

### Outils de Validation
- [ ] Postman/Thunder Client pour tests API
- [ ] pgAdmin pour vérification schémas
- [ ] Logs centralisés pour débogage
- [ ] Monitoring basique des performances

### Backup Strategy
- [ ] Dump PostgreSQL avant Phase 2
- [ ] Sauvegarde code avant modifications
- [ ] Scripts de rollback préparés
- [ ] Documentation de récupération

## 📋 Checklist de Validation Finale

### ✅ Intégration API Gateway
- [ ] Service library configuré dans SERVICES
- [ ] Routes mappées dans LEGACY_ROUTE_MAPPING  
- [ ] Health check accessible via Gateway
- [ ] Proxy des requêtes fonctionnel

### ✅ Architecture Multi-Tenant
- [ ] Middleware uniforme avec CRM/Document
- [ ] Communication avec tenant-service
- [ ] Isolation schémas validée
- [ ] Pas de création automatique de tenants

### ✅ Authentication Alignment
- [ ] Permissions AllowAny configurées
- [ ] JWT géré par API Gateway uniquement
- [ ] Headers X-User-ID/X-Tenant-ID propagés
- [ ] Tests authentification passants

### ✅ Cohérence des Modèles
- [ ] Modèle Client simplifié et uniforme
- [ ] Migrations appliquées sans erreur
- [ ] Pas de données perdues
- [ ] Structure identique aux autres services

### ✅ Tests et Validation
- [ ] CRUD complet via API Gateway
- [ ] Frontend peut consommer les API
- [ ] Tests multi-tenant passants
- [ ] Pas de régression sur autres services
- [ ] Documentation mise à jour

---

## 🚀 Commandes de Démarrage Post-Refactorisation

```bash
# 1. Démarrer tous les services
cd soa/services/tenant-service && python manage.py runserver 0.0.0.0:8001 &
cd soa/services/auth-service && python manage.py runserver 0.0.0.0:8002 &  
cd soa/services/crm-service && python manage.py runserver 0.0.0.0:8003 &
cd soa/services/document-service && python manage.py runserver 0.0.0.0:8004 &
cd soa/services/library-service && python manage.py runserver 0.0.0.0:8005 &

# 2. Démarrer API Gateway
cd soa/api-gateway && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

# 3. Démarrer Frontend  
cd beena && npm run dev &

# 4. Tests de validation
curl http://localhost:8000/health/
curl -H "X-Tenant-ID: <uuid>" http://localhost:8000/api/library/categories/
```

---

*Ce plan sera mis à jour au fur et à mesure de l'avancement. Chaque phase doit être validée avant de passer à la suivante.*