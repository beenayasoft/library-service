"""
Utilitaires pour optimiser les requêtes N+1 via prefetch_related personnalisé.
Créé pour corriger le problème de performance dans IngredientOuvrageSerializer.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from .models import Fourniture, MainOeuvre, IngredientOuvrage


class IngredientElementPrefetch(models.Prefetch):
    """
    Prefetch personnalisé pour précharger les fournitures et main d'œuvre
    des ingrédients d'ouvrages en une seule requête par type.
    
    Évite les requêtes N+1 dans IngredientOuvrageSerializer.
    """
    
    def __init__(self):
        super().__init__('ingredients')
    
    def get_prefetch_queryset(self, instances, queryset=None):
        """
        Précharge toutes les fournitures et main d'œuvre des ingredients 
        puis les injecte dans les objets IngredientOuvrage.
        """
        if queryset is None:
            queryset = IngredientOuvrage.objects.all()
        
        # Récupérer tous les ingredients pour les ouvrages donnés
        ouvrage_ids = [instance.pk for instance in instances]
        ingredients = list(queryset.filter(ouvrage_id__in=ouvrage_ids).select_related('element_type'))
        
        if not ingredients:
            return queryset.none(), None, lambda obj_list, *args: None, True
        
        # Grouper par type d'élément
        fourniture_ids = []
        mainoeuvre_ids = []
        
        for ingredient in ingredients:
            if ingredient.element_type.model == 'fourniture':
                fourniture_ids.append(ingredient.element_id)
            elif ingredient.element_type.model == 'mainoeuvre':
                mainoeuvre_ids.append(ingredient.element_id)
        
        # Précharger toutes les fournitures d'un coup
        fournitures_data = {}
        if fourniture_ids:
            fournitures = Fourniture.objects.filter(id__in=fourniture_ids).only(
                'id', 'nom', 'unite', 'prix_achat_ht'
            )
            fournitures_data = {
                f.id: {
                    'nom': f.nom,
                    'unite': f.unite, 
                    'prix_achat_ht': f.prix_achat_ht
                }
                for f in fournitures
            }
        
        # Précharger toutes les main d'œuvre d'un coup
        mainoeuvre_data = {}
        if mainoeuvre_ids:
            mainoeuvres = MainOeuvre.objects.filter(id__in=mainoeuvre_ids).only(
                'id', 'nom', 'unite', 'cout_horaire'
            )
            mainoeuvre_data = {
                mo.id: {
                    'nom': mo.nom,
                    'unite': mo.unite,
                    'cout_horaire': mo.cout_horaire
                }
                for mo in mainoeuvres
            }
        
        # Injecter les données préchargées dans chaque ingredient
        for ingredient in ingredients:
            if ingredient.element_type.model == 'fourniture':
                element_data = fournitures_data.get(ingredient.element_id, {})
            elif ingredient.element_type.model == 'mainoeuvre':
                element_data = mainoeuvre_data.get(ingredient.element_id, {})
            else:
                element_data = {}
            
            # Injecter les données préchargées (utilisées par IngredientOuvrageSerializer)
            ingredient._prefetched_element_data = element_data
        
        def assign_ingredients(obj_list, ingredients_qs=None):
            """Assigne les ingredients préchargés aux ouvrages"""
            ouvrage_ingredients = {}
            for ingredient in ingredients:
                if ingredient.ouvrage_id not in ouvrage_ingredients:
                    ouvrage_ingredients[ingredient.ouvrage_id] = []
                ouvrage_ingredients[ingredient.ouvrage_id].append(ingredient)
            
            for ouvrage in obj_list:
                ouvrage._prefetched_objects_cache = ouvrage._prefetched_objects_cache or {}
                ouvrage._prefetched_objects_cache['ingredients'] = ouvrage_ingredients.get(ouvrage.pk, [])
        
        return queryset.filter(id__in=[i.id for i in ingredients]), assign_ingredients, lambda obj_list, *args: None, True


def get_optimized_ouvrages_queryset():
    """
    Retourne un QuerySet optimisé pour les ouvrages avec préchargement
    des ingredients et de leurs éléments (fournitures/main d'œuvre).
    
    Utilisation dans les ViewSets:
    ouvrages_qs = get_optimized_ouvrages_queryset()
    """
    return models.QuerySet().prefetch_related(
        IngredientElementPrefetch()
    ).select_related('categorie')


def optimize_ingredients_queryset(ingredients_list):
    """
    Optimise une liste d'objets IngredientOuvrage en préchargeant 
    les fournitures et main d'œuvre en batch.
    
    Usage:
    ingredients = [ingredient1, ingredient2, ...]
    optimize_ingredients_queryset(ingredients)  # Modifie en place
    """
    if not ingredients_list:
        return
    
    # Séparer par type
    fourniture_ids = []
    mainoeuvre_ids = []
    
    for ingredient in ingredients_list:
        if ingredient.element_type.model == 'fourniture':
            fourniture_ids.append(ingredient.element_id)
        elif ingredient.element_type.model == 'mainoeuvre':
            mainoeuvre_ids.append(ingredient.element_id)
    
    # Précharger toutes les données d'un coup
    fournitures_data = {}
    if fourniture_ids:
        fournitures = Fourniture.objects.filter(id__in=fourniture_ids).only(
            'id', 'nom', 'unite', 'prix_achat_ht'
        )
        fournitures_data = {f.id: {'nom': f.nom, 'unite': f.unite, 'prix_achat_ht': f.prix_achat_ht} for f in fournitures}
    
    mainoeuvre_data = {}
    if mainoeuvre_ids:
        mainoeuvres = MainOeuvre.objects.filter(id__in=mainoeuvre_ids).only(
            'id', 'nom', 'unite', 'cout_horaire'
        )
        mainoeuvre_data = {mo.id: {'nom': mo.nom, 'unite': mo.unite, 'cout_horaire': mo.cout_horaire} for mo in mainoeuvres}
    
    # Injecter les données dans chaque ingredient
    for ingredient in ingredients_list:
        if ingredient.element_type.model == 'fourniture':
            element_data = fournitures_data.get(ingredient.element_id, {})
        elif ingredient.element_type.model == 'mainoeuvre':
            element_data = mainoeuvre_data.get(ingredient.element_id, {})
        else:
            element_data = {}
        
        ingredient._prefetched_element_data = element_data