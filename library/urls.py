from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategorieViewSet, 
    FournitureViewSet, 
    MainOeuvreViewSet, 
    OuvrageViewSet,
    IngredientOuvrageViewSet,
    LibrarySearchViewSet
)

# Configuration du router DRF
router = DefaultRouter()
router.register(r'categories', CategorieViewSet)
router.register(r'fournitures', FournitureViewSet)
router.register(r'main-oeuvre', MainOeuvreViewSet)
router.register(r'ouvrages', OuvrageViewSet)
router.register(r'ingredients', IngredientOuvrageViewSet)
router.register(r'search', LibrarySearchViewSet, basename='library-search')

urlpatterns = [
    # API REST
    path('', include(router.urls)),
]

# URLs spécifiques aux actions personnalisées  
app_name = 'library'