# 🔧 Phase 2 - Guide de Test du Middleware Tenant

## ⚠️ IMPORTANT - Modifications Effectuées

### Changements dans library-service:
1. **Nouveau middleware** : `library/middleware.py` (uniforme avec CRM/Document)
2. **Settings modifiés** : Middleware, cache, tenant-service URL
3. **Dépendance ajoutée** : `requests==2.31.0` dans requirements.txt
4. **Ancien middleware sauvegardé** : `middleware_hybrid.py.backup`

### Avant de tester:
```bash
cd soa/services/library-service
pip install requests==2.31.0  # Si pas déjà installé
```

## 🚀 Démarrage des Services (Ordre Important)

### Terminal 1 - Tenant Service (OBLIGATOIRE pour Phase 2)
```bash
cd soa/services/tenant-service
python manage.py runserver 0.0.0.0:8001
```

### Terminal 2 - Library Service (avec nouveau middleware)
```bash
cd soa/services/library-service
python manage.py runserver 0.0.0.0:8005
```

### Terminal 3 - API Gateway (optionnel pour Phase 2)
```bash
cd soa/api-gateway
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Tests Phase 2

### Test 1: Vérification du nouveau middleware
```bash
cd soa/services/library-service
python test_phase2_middleware.py
```

### Test 2: Tests manuels
```bash
# Test sans header (doit échouer avec 400)
curl http://localhost:8005/api/categories/

# Test avec UUID invalide (doit échouer avec 400)
curl -H "X-Tenant-ID: invalid" http://localhost:8005/api/categories/

# Test endpoint public (doit marcher)
curl http://localhost:8005/health/

# Test avec UUID valide mais inexistant (doit échouer avec 401)
curl -H "X-Tenant-ID: 123e4567-e89b-12d3-a456-426614174000" http://localhost:8005/api/categories/
```

## 🔍 Résolution de Problèmes

### Erreur "Missing X-Tenant-ID header"
✅ **Normal** - Le middleware fonctionne correctement

### Erreur "Tenant service unavailable" 
❌ **Problème** - Vérifier que tenant-service tourne sur port 8001

### Erreur "Invalid tenant ID"
✅ **Normal** - Le tenant n'existe pas dans tenant-service

### Erreur d'import dans le middleware
❌ **Problème** - Vérifier les installations:
```bash
pip install requests django-tenants
```

### Erreur de migration
❌ **Problème** - Appliquer les migrations:
```bash
python manage.py migrate
```

## 📊 Indicateurs de Succès Phase 2

### ✅ Critères OBLIGATOIRES:
- [ ] Library service démarre sans erreur
- [ ] Tenant service accessible sur port 8001
- [ ] Requêtes sans X-Tenant-ID rejetées (400)
- [ ] UUID invalides rejetés (400) 
- [ ] Endpoints publics accessibles (/health/)
- [ ] Communication avec tenant-service fonctionne

### ✅ Critères OPTIONNELS:
- [ ] Tests automatisés passent > 80%
- [ ] Logs du middleware informatifs
- [ ] Cache tenant fonctionne
- [ ] Création automatique de tenants (si tenant existe dans tenant-service)

## 📝 Logs à Surveiller

### Library Service:
```bash
tail -f soa/services/library-service/logs/library.log
```

### Tenant Service:
```bash
tail -f soa/services/tenant-service/logs/tenant.log
```

### Middleware Debug:
Dans `library_service/settings.py`, changer temporairement:
```python
'loggers': {
    'library': {
        'level': 'DEBUG',  # Au lieu de 'INFO'
    }
}
```

## 🎯 Objectifs Phase 2

1. **✅ Uniformité** : Middleware identique à CRM/Document
2. **✅ Sécurité** : Validation stricte des tenants
3. **✅ Communication** : Intégration avec tenant-service  
4. **✅ Isolation** : Séparation correcte des schémas
5. **✅ Performance** : Cache des infos tenant

Une fois la Phase 2 validée, nous passerons à la **Phase 3 - Authentication Alignment**.

## 🚑 Rollback si Problèmes

Si la Phase 2 ne fonctionne pas:

```bash
# Restaurer l'ancien middleware
cd soa/services/library-service/library
cp middleware_hybrid.py.backup middleware_hybrid.py

# Restaurer settings.py (changer dans MIDDLEWARE)
# 'library.middleware.HeaderTenantMiddleware' 
# → 'library.middleware_hybrid.HeaderTenantMiddleware'
```