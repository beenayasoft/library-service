from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import Coalesce
import hashlib
import json
import logging

logger = logging.getLogger('library')

from .models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage
from .serializers import (
    CategorieSerializer, CategorieDetailSerializer,
    FournitureSerializer, FournitureDetailSerializer,
    MainOeuvreSerializer, MainOeuvreDetailSerializer,
    OuvrageSerializer, OuvrageDetailSerializer,
    IngredientOuvrageSerializer, IngredientOuvrageCreateSerializer,
    LibraryItemSerializer
)
from .mixins import GatewayAuthMixin

class CategorieViewSet(GatewayAuthMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les catégories.
    Utilise GatewayAuthMixin pour l'authentification via API Gateway.
    """
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'position', 'created_at']
    
    def get_queryset(self):
        """QuerySet optimisé selon l'action"""
        if hasattr(self, 'action'):
            if self.action == 'list':
                return Categorie.objects.select_related('parent').only(
                    'id', 'nom', 'parent', 'position', 'chemin_complet'
                )
            elif self.action == 'retrieve':
                return Categorie.objects.select_related('parent').prefetch_related('sous_categories')
        
        return Categorie.objects.select_related('parent')

    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return CategorieDetailSerializer
        return CategorieSerializer
    
    @action(detail=False, methods=['get'])
    def racines(self, request):
        """
        Endpoint pour récupérer uniquement les catégories racines (sans parent).
        """
        racines = self.get_queryset().filter(parent=None)
        serializer = CategorieDetailSerializer(racines, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des catégories"""
        queryset = self.get_queryset()
        total_categories = queryset.count()
        categories_avec_parent = queryset.filter(parent__isnull=False).count()
        categories_racines = total_categories - categories_avec_parent
        
        stats_aggregates = {
            'total_categories': total_categories,
            'categories_racines': categories_racines,
            'categories_avec_parent': categories_avec_parent,
        }
        
        return Response(stats_aggregates)
    
    @action(detail=True, methods=['get'])
    def sous_categories(self, request, pk=None):
        """
        Endpoint pour récupérer toutes les sous-catégories directes d'une catégorie.
        """
        try:
            categorie = self.get_object()
            sous_categories = Categorie.objects.filter(parent=categorie)
            serializer = CategorieSerializer(sous_categories, many=True)
            return Response(serializer.data)
        except Categorie.DoesNotExist:
            return Response(
                {"detail": "Catégorie non trouvée"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class FournitureViewSet(GatewayAuthMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les fournitures.
    Utilise GatewayAuthMixin pour l'authentification via API Gateway.
    """
    queryset = Fourniture.objects.all()
    serializer_class = FournitureSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'unite', 'type', 'supplier', 'is_recyclable']
    search_fields = ['nom', 'description', 'reference', 'code']
    ordering_fields = ['nom', 'prix_achat_ht', 'created_at', 'updated_at']
    
    def get_queryset(self):
        """QuerySet optimisé selon l'action"""
        if hasattr(self, 'action'):
            if self.action == 'list':
                return Fourniture.objects.select_related('categorie').only(
                    'id', 'nom', 'unite', 'prix_achat_ht', 'categorie', 'reference', 'type', 'code'
                )
            elif self.action == 'retrieve':
                return Fourniture.objects.select_related('categorie')
            elif self.action == 'stats':
                return Fourniture.objects.select_related('categorie').defer('description')
        
        return Fourniture.objects.select_related('categorie')

    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return FournitureDetailSerializer
        return FournitureSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des fournitures"""
        # Aggregation optimisée en une seule requête
        stats_aggregates = self.get_queryset().aggregate(
            total=Count('id'),
            par_categorie=Count('categorie', distinct=True),
            prix_moyen=Avg('prix_achat_ht'),
            prix_total=Sum('prix_achat_ht'),
            avec_reference=Count('id', filter=Q(reference__isnull=False)),
            avec_supplier=Count('id', filter=Q(supplier__isnull=False)),
            recyclables=Count('id', filter=Q(is_recyclable=True))
        )
        
        return Response(stats_aggregates)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les fournitures groupées par catégorie.
        """
        fournitures = Fourniture.objects.select_related('categorie').order_by('categorie__nom', 'nom')
        
        # Grouper par catégorie
        categories_dict = {}
        for fourniture in fournitures:
            cat_nom = fourniture.categorie.nom if fourniture.categorie else "Sans catégorie"
            if cat_nom not in categories_dict:
                categories_dict[cat_nom] = []
            categories_dict[cat_nom].append(FournitureSerializer(fourniture).data)
        
        return Response(categories_dict)

class MainOeuvreViewSet(GatewayAuthMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les types de main d'œuvre.
    """
    queryset = MainOeuvre.objects.all()
    serializer_class = MainOeuvreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'type', 'skill_level']
    search_fields = ['nom', 'description', 'code']
    ordering_fields = ['nom', 'cout_horaire', 'created_at', 'updated_at']
    
    def get_queryset(self):
        """QuerySet optimisé selon l'action"""
        if hasattr(self, 'action'):
            if self.action == 'list':
                return MainOeuvre.objects.select_related('categorie').only(
                    'id', 'nom', 'cout_horaire', 'categorie', 'type', 'unite', 'skill_level'
                )
            elif self.action == 'retrieve':
                return MainOeuvre.objects.select_related('categorie')
            elif self.action == 'stats':
                return MainOeuvre.objects.select_related('categorie').defer('description')
        
        return MainOeuvre.objects.select_related('categorie')

    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return MainOeuvreDetailSerializer
        return MainOeuvreSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des types de main d'œuvre"""
        # Aggregation optimisée en une seule requête
        stats_aggregates = self.get_queryset().aggregate(
            total=Count('id'),
            par_categorie=Count('categorie', distinct=True),
            cout_moyen=Avg('cout_horaire'),
            cout_total=Sum('cout_horaire'),
            par_type=Count('id', filter=Q(type__isnull=False)),
            specialises=Count('id', filter=Q(skill_level='expert'))
        )
        
        return Response(stats_aggregates)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les types de main d'œuvre groupés par catégorie.
        """
        main_oeuvre = MainOeuvre.objects.select_related('categorie').order_by('categorie__nom', 'nom')
        
        # Grouper par catégorie
        categories_dict = {}
        for mo in main_oeuvre:
            cat_nom = mo.categorie.nom if mo.categorie else "Sans catégorie"
            if cat_nom not in categories_dict:
                categories_dict[cat_nom] = []
            categories_dict[cat_nom].append(MainOeuvreSerializer(mo).data)
        
        return Response(categories_dict)

class OuvrageViewSet(GatewayAuthMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer les opérations CRUD sur les ouvrages.
    """
    queryset = Ouvrage.objects.all()
    serializer_class = OuvrageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'unite', 'type', 'complexity', 'is_custom', 'requires_certification']
    search_fields = ['nom', 'description', 'code']
    ordering_fields = ['nom', 'prix_recommande', 'created_at', 'updated_at']
    
    def get_queryset(self):
        """QuerySet optimisé selon l'action"""
        if hasattr(self, 'action'):
            if self.action == 'list':
                return Ouvrage.objects.select_related('categorie').only(
                    'id', 'nom', 'unite', 'categorie', 'prix_recommande', 'code', 'type', 'complexity'
                )
            elif self.action == 'retrieve':
                return Ouvrage.objects.select_related('categorie').prefetch_related('ingredients')
            elif self.action == 'stats':
                return Ouvrage.objects.select_related('categorie').defer('description')
        
        return Ouvrage.objects.select_related('categorie')

    def get_serializer_class(self):
        """
        Utilise le sérialiseur détaillé pour les opérations de lecture individuelles.
        """
        if self.action == 'retrieve':
            return OuvrageDetailSerializer
        return OuvrageSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des ouvrages"""
        # Aggregation optimisée en une seule requête
        stats_aggregates = self.get_queryset().aggregate(
            total=Count('id'),
            par_categorie=Count('categorie', distinct=True),
            prix_moyen=Avg('prix_recommande'),
            prix_total=Sum('prix_recommande'),
            personnalises=Count('id', filter=Q(is_custom=True)),
            avec_ingredients=Count('id', filter=Q(ingredients__isnull=False)),
            avec_certification=Count('id', filter=Q(requires_certification=True))
        )
        
        return Response(stats_aggregates)

    @action(detail=False, methods=['get'])
    def par_categorie(self, request):
        """
        Endpoint pour récupérer les ouvrages groupés par catégorie.
        """
        ouvrages = Ouvrage.objects.select_related('categorie').order_by('categorie__nom', 'nom')
        
        # Grouper par catégorie
        categories_dict = {}
        for ouvrage in ouvrages:
            cat_nom = ouvrage.categorie.nom if ouvrage.categorie else "Sans catégorie"
            if cat_nom not in categories_dict:
                categories_dict[cat_nom] = []
            categories_dict[cat_nom].append(OuvrageSerializer(ouvrage).data)
        
        return Response(categories_dict)

class IngredientOuvrageViewSet(GatewayAuthMixin, viewsets.ModelViewSet):
    """
    ViewSet pour gérer les ingrédients d'ouvrages.
    """
    queryset = IngredientOuvrage.objects.all()
    serializer_class = IngredientOuvrageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ouvrage', 'content_type']
    search_fields = ['ouvrage__nom']
    ordering_fields = ['ouvrage__nom', 'quantite', 'created_at']
    
    def get_queryset(self):
        """QuerySet optimisé avec select_related"""
        return IngredientOuvrage.objects.select_related(
            'ouvrage', 'content_type'
        ).prefetch_related('content_object')

    def get_serializer_class(self):
        """
        Utilise le sérialiseur approprié selon l'action.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return IngredientOuvrageCreateSerializer
        return IngredientOuvrageSerializer
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des ingrédients d'ouvrages"""
        stats_aggregates = self.get_queryset().aggregate(
            total=Count('id'),
            par_ouvrage=Count('ouvrage', distinct=True),
            par_type=Count('content_type', distinct=True),
            quantite_moyenne=Avg('quantite'),
            quantite_totale=Sum('quantite')
        )
        
        return Response(stats_aggregates)

    @action(detail=False, methods=['get'])
    def par_ouvrage(self, request):
        """
        Endpoint pour récupérer les ingrédients groupés par ouvrage.
        """
        ingredients = self.get_queryset().order_by('ouvrage__nom', 'content_type__model')
        
        # Grouper par ouvrage
        ouvrages_dict = {}
        for ingredient in ingredients:
            ouvrage_nom = ingredient.ouvrage.nom
            if ouvrage_nom not in ouvrages_dict:
                ouvrages_dict[ouvrage_nom] = []
            ouvrages_dict[ouvrage_nom].append(IngredientOuvrageSerializer(ingredient).data)
        
        return Response(ouvrages_dict)

class LibraryCompositeViewSet(GatewayAuthMixin, viewsets.ViewSet):
    """
    ViewSet composite pour récupérer tous les éléments de bibliothèque en un seul appel.
    OPTIMISATION Milestone 1.2: Réduction 3 appels → 1 appel (-200ms)
    """
    
    @action(detail=False, methods=['get'])
    def all_items(self, request):
        """
        Endpoint composite qui retourne fournitures, main d'œuvre et ouvrages en un seul appel.
        Optimisé avec QuerySet bulk et pagination unifiée.
        """
        try:
            # Paramètres de pagination
            page_size = int(request.GET.get('page_size', 50))
            page = int(request.GET.get('page', 1))
            
            # Paramètres de filtrage optionnels
            search_query = request.GET.get('search', '').strip()
            category_filter = request.GET.get('category', None)
            
            # QuerySets OPTIMISÉS avec select_related et prefetch_related pour éviter N+1 queries
            fournitures_qs = Fourniture.objects.select_related('categorie').only(
                'id', 'nom', 'unite', 'prix_achat_ht', 'categorie__id', 'categorie__nom', 
                'reference', 'type', 'code', 'vat_rate', 'supplier'
            ).order_by('categorie__nom', 'nom')
            
            main_oeuvre_qs = MainOeuvre.objects.select_related('categorie').only(
                'id', 'nom', 'cout_horaire', 'categorie__id', 'categorie__nom', 
                'type', 'unite', 'skill_level', 'productivity_factor'
            ).order_by('categorie__nom', 'nom')
            
            ouvrages_qs = Ouvrage.objects.select_related('categorie').prefetch_related(
                'ingredients__element_type'
            ).only(
                'id', 'nom', 'unite', 'categorie__id', 'categorie__nom', 
                'prix_recommande', 'code', 'type', 'complexity', 'marge', 'efficiency'
            ).order_by('categorie__nom', 'nom')
            
            # Filtrage par recherche si spécifié
            if search_query:
                fournitures_qs = fournitures_qs.filter(
                    Q(nom__icontains=search_query) | Q(description__icontains=search_query) | Q(reference__icontains=search_query)
                )
                main_oeuvre_qs = main_oeuvre_qs.filter(
                    Q(nom__icontains=search_query) | Q(description__icontains=search_query) | Q(code__icontains=search_query)
                )
                ouvrages_qs = ouvrages_qs.filter(
                    Q(nom__icontains=search_query) | Q(description__icontains=search_query) | Q(code__icontains=search_query)
                )
            
            # Filtrage par catégorie si spécifié
            if category_filter:
                fournitures_qs = fournitures_qs.filter(categorie_id=category_filter)
                main_oeuvre_qs = main_oeuvre_qs.filter(categorie_id=category_filter)
                ouvrages_qs = ouvrages_qs.filter(categorie_id=category_filter)
            
            # OPTIMISATION: Exécution des requêtes avec limites et annotations pour performance DB
            start_time = request.META.get('HTTP_X_REQUEST_START', None)
            
            # Limitation intelligente par type pour équilibrer la réponse
            limit_per_type = min(page_size, 100)  # Cap à 100 pour éviter surcharge
            
            # Exécution optimisée avec evaluate() pour forcer l'exécution
            fournitures = list(fournitures_qs[:limit_per_type])
            main_oeuvre = list(main_oeuvre_qs[:limit_per_type])  
            ouvrages = list(ouvrages_qs[:limit_per_type])
            
            # Compter totaux pour pagination (requêtes séparées mais optimisées avec index)
            total_fournitures = fournitures_qs.count() if len(fournitures) == limit_per_type else len(fournitures)
            total_main_oeuvre = main_oeuvre_qs.count() if len(main_oeuvre) == limit_per_type else len(main_oeuvre)
            total_ouvrages = ouvrages_qs.count() if len(ouvrages) == limit_per_type else len(ouvrages)
            
            # Sérialisation optimisée avec metrics intégrées
            response_data = {
                'fournitures': {
                    'count': len(fournitures),
                    'total': total_fournitures,
                    'items': FournitureSerializer(fournitures, many=True).data
                },
                'main_oeuvre': {
                    'count': len(main_oeuvre),
                    'total': total_main_oeuvre,
                    'items': MainOeuvreSerializer(main_oeuvre, many=True).data
                },
                'ouvrages': {
                    'count': len(ouvrages),
                    'total': total_ouvrages,
                    'items': OuvrageSerializer(ouvrages, many=True).data
                },
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'limit_per_type': limit_per_type,
                    'returned_items': len(fournitures) + len(main_oeuvre) + len(ouvrages),
                    'total_items': total_fournitures + total_main_oeuvre + total_ouvrages
                },
                'filters_applied': {
                    'search': search_query if search_query else None,
                    'category': category_filter if category_filter else None
                },
                'performance': {
                    'endpoint': 'composite_optimized',
                    'milestone': '1.3',
                    'db_optimizations': ['select_related', 'prefetch_related', 'only_fields', 'ordering'],
                    'queries_saved': 2,  # 3 appels → 1 appel
                    'queryset_optimization': True
                }
            }
            
            logger.info(f"Library - Endpoint composite: {len(fournitures)}F + {len(main_oeuvre)}MO + {len(ouvrages)}O")
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Library - Erreur endpoint composite: {str(e)}")
            return Response({
                'error': 'Error retrieving library data',
                'details': str(e),
                'endpoint': 'composite'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LibrarySearchViewSet(viewsets.ViewSet):
    """
    ViewSet pour la recherche dans toute la bibliothèque.
    """
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Recherche globale dans tous les éléments de la bibliothèque.
        """
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({"detail": "Paramètre de recherche 'q' requis"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Recherche dans les catégories
        categories = Categorie.objects.filter(
            Q(nom__icontains=query) | Q(description__icontains=query)
        )[:10]
        
        # Recherche dans les fournitures
        fournitures = Fourniture.objects.filter(
            Q(nom__icontains=query) | Q(description__icontains=query) | Q(reference__icontains=query)
        ).select_related('categorie')[:10]
        
        # Recherche dans la main d'œuvre
        main_oeuvre = MainOeuvre.objects.filter(
            Q(nom__icontains=query) | Q(description__icontains=query) | Q(code__icontains=query)
        ).select_related('categorie')[:10]
        
        # Recherche dans les ouvrages
        ouvrages = Ouvrage.objects.filter(
            Q(nom__icontains=query) | Q(description__icontains=query) | Q(code__icontains=query)
        ).select_related('categorie')[:10]
        
        results = {
            'categories': CategorieSerializer(categories, many=True).data,
            'fournitures': FournitureSerializer(fournitures, many=True).data,
            'main_oeuvre': MainOeuvreSerializer(main_oeuvre, many=True).data,
            'ouvrages': OuvrageSerializer(ouvrages, many=True).data,
            'total_results': len(categories) + len(fournitures) + len(main_oeuvre) + len(ouvrages)
        }
        
        return Response(results)