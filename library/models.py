from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Categorie(models.Model):
    """
    Modèle pour représenter les catégories hiérarchiques dans la bibliothèque d'ouvrages.
    Une catégorie peut avoir un parent, créant ainsi une structure arborescente.
    
    Note: Adapté pour django-tenants - pas de tenant_id car isolation par schéma PostgreSQL.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sous_categories',
        verbose_name="Catégorie parente"
    )
    position = models.PositiveIntegerField(default=0, verbose_name="Position d'affichage")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['position', 'nom']
        indexes = [
            # Index simples
            models.Index(fields=['nom']),
            models.Index(fields=['parent']),
            models.Index(fields=['position']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Index composites
            models.Index(fields=['parent', 'position']),
            models.Index(fields=['parent', 'nom']),
            models.Index(fields=['position', 'nom']),
            models.Index(fields=['created_at', 'updated_at']),
        ]
    
    def __str__(self):
        return self.nom
    
    @property
    def chemin_complet(self):
        """
        Retourne le chemin complet de la catégorie (ex: "Maçonnerie > Murs")
        """
        if self.parent:
            return f"{self.parent.chemin_complet} > {self.nom}"
        return self.nom

class Fourniture(models.Model):
    """
    Modèle pour représenter les fournitures (matériaux, produits, etc.) utilisées dans les ouvrages.
    
    Note: Adapté pour django-tenants - pas de tenant_id car isolation par schéma PostgreSQL.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom de la fourniture")
    unite = models.CharField(max_length=20, verbose_name="Unité de mesure")
    prix_achat_ht = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Prix d'achat HT"
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='fournitures',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    reference = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Référence"
    )
    supplier = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Fournisseur"
    )
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0,
        verbose_name="Taux TVA (%)"
    )
    # Champs pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="material",
        verbose_name="Type"
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code"
    )
    # Champs additionnels pour BTP
    waste_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        verbose_name="Facteur de perte (%)"
    )
    is_recyclable = models.BooleanField(
        default=False,
        verbose_name="Recyclable"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Fourniture"
        verbose_name_plural = "Fournitures"
        ordering = ['nom']
        indexes = [
            # Index simples
            models.Index(fields=['nom']),
            models.Index(fields=['unite']),
            models.Index(fields=['prix_achat_ht']),
            models.Index(fields=['categorie']),
            models.Index(fields=['reference']),
            models.Index(fields=['supplier']),
            models.Index(fields=['vat_rate']),
            models.Index(fields=['type']),
            models.Index(fields=['code']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Index composites
            models.Index(fields=['categorie', 'nom']),
            models.Index(fields=['categorie', 'prix_achat_ht']),
            models.Index(fields=['type', 'categorie']),
            models.Index(fields=['unite', 'categorie']),
            models.Index(fields=['supplier', 'nom']),
            models.Index(fields=['vat_rate', 'prix_achat_ht']),
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['categorie', 'type', 'nom']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.unite})"
    
    @property
    def unitPrice(self):
        """Alias pour prix_achat_ht (compatibilité frontend)"""
        return self.prix_achat_ht
    
    @property
    def vatRate(self):
        """Alias pour vat_rate (compatibilité frontend)"""
        return float(self.vat_rate)
    
    @property
    def wasteFactor(self):
        """Alias pour waste_factor (compatibilité frontend)"""
        return float(self.waste_factor)

class MainOeuvre(models.Model):
    """
    Modèle pour représenter les différents types de main d'œuvre avec leur coût horaire.
    
    Note: Adapté pour django-tenants - pas de tenant_id car isolation par schéma PostgreSQL.
    """
    nom = models.CharField(max_length=100, verbose_name="Nom du type de main d'œuvre")
    cout_horaire = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Coût horaire"
    )
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='main_oeuvre',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    # Champs pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="labor",
        verbose_name="Type"
    )
    unite = models.CharField(
        max_length=20,
        default="h",
        verbose_name="Unité de mesure"
    )
    code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Code"
    )
    # Champs additionnels pour BTP
    skill_level = models.CharField(
        max_length=20,
        choices=[
            ('apprentice', 'Apprenti'),
            ('skilled', 'Qualifié'),
            ('expert', 'Expert'),
            ('specialist', 'Spécialiste')
        ],
        default='skilled',
        verbose_name="Niveau de qualification"
    )
    productivity_factor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name="Facteur de productivité"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Main d'œuvre"
        verbose_name_plural = "Main d'œuvre"
        ordering = ['nom']
        indexes = [
            # Index simples
            models.Index(fields=['nom']),
            models.Index(fields=['cout_horaire']),
            models.Index(fields=['categorie']),
            models.Index(fields=['type']),
            models.Index(fields=['unite']),
            models.Index(fields=['code']),
            models.Index(fields=['skill_level']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Index composites
            models.Index(fields=['categorie', 'nom']),
            models.Index(fields=['categorie', 'cout_horaire']),
            models.Index(fields=['type', 'categorie']),
            models.Index(fields=['unite', 'cout_horaire']),
            models.Index(fields=['skill_level', 'cout_horaire']),
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['categorie', 'type', 'nom']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.cout_horaire}€/h)"
    
    @property
    def unitPrice(self):
        """Alias pour cout_horaire (compatibilité frontend)"""
        return self.cout_horaire
    
    @property
    def prix_achat_ht(self):
        """Alias pour cout_horaire (compatibilité)"""
        return self.cout_horaire

class Ouvrage(models.Model):
    """
    Modèle pour représenter les ouvrages composés, qui sont des assemblages
    d'ingrédients (fournitures et main d'œuvre) avec leurs quantités.
    
    Note: Adapté pour django-tenants - pas de tenant_id car isolation par schéma PostgreSQL.
    """
    nom = models.CharField(max_length=200, verbose_name="Nom de l'ouvrage")
    unite = models.CharField(max_length=20, verbose_name="Unité de mesure")
    categorie = models.ForeignKey(
        Categorie, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ouvrages',
        verbose_name="Catégorie"
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Code/Référence"
    )
    
    prix_recommande = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Prix recommandé"
    )
    marge = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=20.0,
        verbose_name="Marge (%)"
    )
    is_custom = models.BooleanField(
        default=False,
        verbose_name="Ouvrage personnalisé"
    )
    # Champs additionnels pour cohérence frontend
    type = models.CharField(
        max_length=20,
        default="work",
        verbose_name="Type"
    )
    complexity = models.CharField(
        max_length=20,
        choices=[('low', 'Faible'), ('medium', 'Moyenne'), ('high', 'Élevée')],
        default='medium',
        verbose_name="Complexité"
    )
    efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        verbose_name="Rendement"
    )
    # Champs additionnels pour BTP
    duration_estimate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Durée estimée (heures)"
    )
    requires_certification = models.BooleanField(
        default=False,
        verbose_name="Nécessite une certification"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Ouvrage"
        verbose_name_plural = "Ouvrages"
        ordering = ['nom']
        indexes = [
            # Index simples
            models.Index(fields=['nom']),
            models.Index(fields=['unite']),
            models.Index(fields=['categorie']),
            models.Index(fields=['code']),
            models.Index(fields=['prix_recommande']),
            models.Index(fields=['marge']),
            models.Index(fields=['is_custom']),
            models.Index(fields=['type']),
            models.Index(fields=['complexity']),
            models.Index(fields=['efficiency']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Index composites
            models.Index(fields=['categorie', 'nom']),
            models.Index(fields=['categorie', 'prix_recommande']),
            models.Index(fields=['type', 'categorie']),
            models.Index(fields=['complexity', 'categorie']),
            models.Index(fields=['is_custom', 'categorie']),
            models.Index(fields=['unite', 'categorie']),
            models.Index(fields=['marge', 'prix_recommande']),
            models.Index(fields=['efficiency', 'complexity']),
            models.Index(fields=['created_at', 'updated_at']),
            models.Index(fields=['categorie', 'type', 'nom']),
            models.Index(fields=['categorie', 'complexity', 'prix_recommande']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.unite})"
    
    @property
    def debourse_sec(self):
        """
        Calcule le déboursé sec (coût total) de l'ouvrage en fonction des ingrédients et quantités.
        OPTIMISÉ: Utilise les données préchargées pour éviter N+1 queries.
        """
        # Vérifier si les ingrédients sont préchargés
        if hasattr(self, '_prefetched_objects_cache') and 'ingredients' in self._prefetched_objects_cache:
            # Utiliser les données préchargées (0 requête DB)
            ingredients = self._prefetched_objects_cache['ingredients']
        else:
            # Fallback: comportement original (1 requête DB)
            ingredients = self.ingredients.all()
        
        total = 0
        for ingredient in ingredients:
            total += ingredient.cout_total
        return total
    
    @property
    def totalCost(self):
        """Alias pour debourse_sec (compatibilité frontend)"""
        return self.debourse_sec
    
    @property
    def recommendedPrice(self):
        """Prix recommandé calculé ou défini manuellement"""
        if self.prix_recommande > 0:
            return self.prix_recommande
        cout_total = self.debourse_sec
        if cout_total > 0:
            return cout_total * (1 + float(self.marge) / 100)
        return 0
    
    @property
    def margin(self):
        """Alias pour marge (compatibilité frontend)"""
        return float(self.marge)
    
    @property
    def laborCost(self):
        """
        Calcule le coût total de la main d'œuvre.
        OPTIMISÉ: Utilise les données préchargées pour éviter N+1 queries.
        """
        # Vérifier si les ingrédients sont préchargés
        if hasattr(self, '_prefetched_objects_cache') and 'ingredients' in self._prefetched_objects_cache:
            # Utiliser les données préchargées (0 requête DB)
            ingredients = self._prefetched_objects_cache['ingredients']
        else:
            # Fallback: comportement original (1 requête DB)
            ingredients = self.ingredients.all()
        
        total = 0
        for ingredient in ingredients:
            if ingredient.element_type.model == 'mainoeuvre':
                total += ingredient.cout_total
        return total
    
    @property
    def materialCost(self):
        """
        Calcule le coût total des matériaux.
        OPTIMISÉ: Utilise les données préchargées pour éviter N+1 queries.
        """
        # Vérifier si les ingrédients sont préchargés
        if hasattr(self, '_prefetched_objects_cache') and 'ingredients' in self._prefetched_objects_cache:
            # Utiliser les données préchargées (0 requête DB)
            ingredients = self._prefetched_objects_cache['ingredients']
        else:
            # Fallback: comportement original (1 requête DB)
            ingredients = self.ingredients.all()
        
        total = 0
        for ingredient in ingredients:
            if ingredient.element_type.model == 'fourniture':
                total += ingredient.cout_total
        return total

class IngredientOuvrage(models.Model):
    """
    Modèle pour représenter les ingrédients d'un ouvrage avec leurs quantités.
    Utilise une relation générique pour pointer soit vers une fourniture, soit vers un type de main d'œuvre.
    
    Note: Adapté pour django-tenants - pas de tenant_id car isolation par schéma PostgreSQL.
    """
    ouvrage = models.ForeignKey(
        Ouvrage, 
        on_delete=models.CASCADE, 
        related_name='ingredients',
        verbose_name="Ouvrage"
    )
    # Champs pour la relation générique
    element_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('fourniture', 'mainoeuvre')},
        verbose_name="Type d'élément"
    )
    element_id = models.PositiveIntegerField(verbose_name="ID de l'élément")
    element = GenericForeignKey('element_type', 'element_id')
    
    quantite = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        verbose_name="Quantité"
    )
    
    # Champs additionnels pour BTP
    waste_allowance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.0,
        verbose_name="Majoration pour pertes (%)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    class Meta:
        verbose_name = "Ingrédient d'ouvrage"
        verbose_name_plural = "Ingrédients d'ouvrage"
        unique_together = ('ouvrage', 'element_type', 'element_id')
        ordering = ['ouvrage', 'element_type', 'element_id']
        indexes = [
            # Index simples
            models.Index(fields=['ouvrage']),
            models.Index(fields=['element_type']),
            models.Index(fields=['element_id']),
            models.Index(fields=['quantite']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Index composites
            models.Index(fields=['ouvrage', 'element_type']),
            models.Index(fields=['ouvrage', 'element_id']),
            models.Index(fields=['element_type', 'element_id']),
            models.Index(fields=['ouvrage', 'quantite']),
            models.Index(fields=['ouvrage', 'element_type', 'element_id']),
            models.Index(fields=['created_at', 'updated_at']),
        ]
    
    def __str__(self):
        return f"{self.element} - {self.quantite}"
    
    @property
    def cout_total(self):
        """
        Calcule le coût total de cet ingrédient (quantité × prix unitaire).
        OPTIMISÉ: Utilise les données préchargées pour éviter N+1 queries.
        """
        # Vérifier si les données d'élément sont préchargées
        if hasattr(self, '_prefetched_element_data'):
            element_data = self._prefetched_element_data
            prix_unitaire = element_data.get('prix_achat_ht') or element_data.get('cout_horaire', 0)
            base_cost = self.quantite * prix_unitaire
        else:
            # Fallback: comportement original avec requêtes DB
            base_cost = 0
            if self.element_type.model == 'fourniture':
                try:
                    fourniture = Fourniture.objects.get(id=self.element_id)
                    base_cost = self.quantite * fourniture.prix_achat_ht
                except Fourniture.DoesNotExist:
                    return 0
            elif self.element_type.model == 'mainoeuvre':
                try:
                    main_oeuvre = MainOeuvre.objects.get(id=self.element_id)
                    base_cost = self.quantite * main_oeuvre.cout_horaire
                except MainOeuvre.DoesNotExist:
                    return 0
        
        # Appliquer la majoration pour pertes si applicable
        if self.waste_allowance > 0:
            base_cost *= (1 + float(self.waste_allowance) / 100)
            
        return base_cost
