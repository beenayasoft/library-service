from django.contrib import admin
from .models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    """
    Administration des catégories hiérarchiques.
    """
    list_display = ('nom', 'parent', 'position', 'created_at')
    list_filter = ('parent', 'created_at')
    search_fields = ('nom', 'description')
    ordering = ('position', 'nom')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'parent', 'position')
        }),
        ('Détails', {
            'fields': ('description',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Fourniture)
class FournitureAdmin(admin.ModelAdmin):
    """
    Administration des fournitures.
    """
    list_display = ('nom', 'unite', 'prix_achat_ht', 'categorie', 'type', 'supplier')
    list_filter = ('categorie', 'type', 'unite', 'is_recyclable', 'created_at')
    search_fields = ('nom', 'description', 'reference', 'code', 'supplier')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'categorie', 'description')
        }),
        ('Caractéristiques techniques', {
            'fields': ('unite', 'type', 'code', 'reference')
        }),
        ('Coûts et TVA', {
            'fields': ('prix_achat_ht', 'vat_rate')
        }),
        ('Fournisseur', {
            'fields': ('supplier',)
        }),
        ('Propriétés BTP', {
            'fields': ('waste_factor', 'is_recyclable')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(MainOeuvre)
class MainOeuvreAdmin(admin.ModelAdmin):
    """
    Administration de la main d'œuvre.
    """
    list_display = ('nom', 'cout_horaire', 'categorie', 'skill_level', 'type')
    list_filter = ('categorie', 'skill_level', 'type', 'created_at')
    search_fields = ('nom', 'description', 'code')
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'categorie', 'description')
        }),
        ('Caractéristiques', {
            'fields': ('type', 'unite', 'code')
        }),
        ('Coût', {
            'fields': ('cout_horaire',)
        }),
        ('Qualification', {
            'fields': ('skill_level', 'productivity_factor')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

class IngredientOuvrageInline(admin.TabularInline):
    """
    Inline pour les ingrédients d'ouvrages.
    """
    model = IngredientOuvrage
    extra = 0
    fields = ('element_type', 'element_id', 'quantite', 'waste_allowance')

@admin.register(Ouvrage)
class OuvrageAdmin(admin.ModelAdmin):
    """
    Administration des ouvrages.
    """
    list_display = ('nom', 'unite', 'categorie', 'complexity', 'prix_recommande', 'is_custom')
    list_filter = ('categorie', 'complexity', 'type', 'is_custom', 'requires_certification', 'created_at')
    search_fields = ('nom', 'description', 'code')
    inlines = [IngredientOuvrageInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'categorie', 'description')
        }),
        ('Caractéristiques', {
            'fields': ('unite', 'type', 'code', 'complexity')
        }),
        ('Coûts et performance', {
            'fields': ('prix_recommande', 'marge', 'efficiency')
        }),
        ('Propriétés BTP', {
            'fields': ('duration_estimate', 'requires_certification', 'is_custom')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(IngredientOuvrage)
class IngredientOuvrageAdmin(admin.ModelAdmin):
    """
    Administration des ingrédients d'ouvrages.
    """
    list_display = ('ouvrage', 'element_type', 'element_id', 'quantite', 'waste_allowance')
    list_filter = ('element_type', 'ouvrage__categorie', 'created_at')
    search_fields = ('ouvrage__nom', 'notes')
    
    fieldsets = (
        ('Relation', {
            'fields': ('ouvrage', 'element_type', 'element_id')
        }),
        ('Quantité', {
            'fields': ('quantite', 'waste_allowance')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
