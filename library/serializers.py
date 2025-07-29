from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Categorie, Fourniture, MainOeuvre, Ouvrage, IngredientOuvrage

class CategorieSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour le modèle Categorie.
    """
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'parent', 'position', 'description', 'created_at', 'updated_at']

class CategorieDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Categorie, incluant le chemin complet
    et les sous-catégories.
    """
    sous_categories = serializers.SerializerMethodField()
    chemin_complet = serializers.CharField(read_only=True)
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'parent', 'position', 'description', 'chemin_complet', 'sous_categories', 'created_at', 'updated_at']
    
    def get_sous_categories(self, obj):
        """
        Récupère les sous-catégories de la catégorie actuelle.
        """
        sous_categories = Categorie.objects.filter(parent=obj)
        return CategorieSerializer(sous_categories, many=True).data

class FournitureSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Fourniture.
    """
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    unitPrice = serializers.DecimalField(source='prix_achat_ht', max_digits=10, decimal_places=2, read_only=True)
    vatRate = serializers.DecimalField(source='vat_rate', max_digits=5, decimal_places=2, read_only=True)
    wasteFactor = serializers.DecimalField(source='waste_factor', max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Fourniture
        fields = [
            'id', 'nom', 'unite', 'prix_achat_ht', 'categorie', 'categorie_nom', 
            'description', 'reference', 'supplier', 'vat_rate', 'type', 'code',
            'waste_factor', 'is_recyclable', 'unitPrice', 'vatRate', 'wasteFactor',
            'created_at', 'updated_at'
        ]
    
    def get_categorie_nom(self, obj):
        """
        Récupère le nom de la catégorie associée à la fourniture.
        """
        if obj.categorie:
            return obj.categorie.chemin_complet
        return None

class FournitureDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Fourniture.
    """
    categorie_details = CategorieSerializer(source='categorie', read_only=True)
    unitPrice = serializers.DecimalField(source='prix_achat_ht', max_digits=10, decimal_places=2, read_only=True)
    vatRate = serializers.DecimalField(source='vat_rate', max_digits=5, decimal_places=2, read_only=True)
    wasteFactor = serializers.DecimalField(source='waste_factor', max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Fourniture
        fields = [
            'id', 'nom', 'unite', 'prix_achat_ht', 'categorie', 'categorie_details',
            'description', 'reference', 'supplier', 'vat_rate', 'type', 'code',
            'waste_factor', 'is_recyclable', 'unitPrice', 'vatRate', 'wasteFactor',
            'created_at', 'updated_at'
        ]

class MainOeuvreSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle MainOeuvre.
    """
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    unitPrice = serializers.DecimalField(source='cout_horaire', max_digits=10, decimal_places=2, read_only=True)
    prix_achat_ht = serializers.DecimalField(source='cout_horaire', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = MainOeuvre
        fields = [
            'id', 'nom', 'cout_horaire', 'categorie', 'categorie_nom', 'description', 
            'type', 'unite', 'code', 'skill_level', 'productivity_factor',
            'unitPrice', 'prix_achat_ht', 'created_at', 'updated_at'
        ]
    
    def get_categorie_nom(self, obj):
        """
        Récupère le nom de la catégorie associée à la main d'œuvre.
        """
        if obj.categorie:
            return obj.categorie.chemin_complet
        return None

class MainOeuvreDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle MainOeuvre.
    """
    categorie_details = CategorieSerializer(source='categorie', read_only=True)
    unitPrice = serializers.DecimalField(source='cout_horaire', max_digits=10, decimal_places=2, read_only=True)
    prix_achat_ht = serializers.DecimalField(source='cout_horaire', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = MainOeuvre
        fields = [
            'id', 'nom', 'cout_horaire', 'categorie', 'categorie_details', 'description', 
            'type', 'unite', 'code', 'skill_level', 'productivity_factor',
            'unitPrice', 'prix_achat_ht', 'created_at', 'updated_at'
        ]

class IngredientOuvrageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle IngredientOuvrage.
    """
    element_nom = serializers.SerializerMethodField()
    element_unite = serializers.SerializerMethodField()
    element_prix = serializers.SerializerMethodField()
    cout_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    element_type_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = IngredientOuvrage
        fields = [
            'id', 'ouvrage', 'element_type', 'element_type_nom', 'element_id', 
            'element_nom', 'element_unite', 'element_prix', 'quantite', 'cout_total',
            'waste_allowance', 'notes', 'created_at', 'updated_at'
        ]
    
    def get_element_nom(self, obj):
        """
        Récupère le nom de l'élément (fourniture ou main d'œuvre).
        """
        if obj.element_type.model == 'fourniture':
            try:
                return Fourniture.objects.get(id=obj.element_id).nom
            except Fourniture.DoesNotExist:
                return None
        elif obj.element_type.model == 'mainoeuvre':
            try:
                return MainOeuvre.objects.get(id=obj.element_id).nom
            except MainOeuvre.DoesNotExist:
                return None
        return None
    
    def get_element_unite(self, obj):
        """
        Récupère l'unité de l'élément (fourniture ou main d'œuvre).
        """
        if obj.element_type.model == 'fourniture':
            try:
                return Fourniture.objects.get(id=obj.element_id).unite
            except Fourniture.DoesNotExist:
                return None
        elif obj.element_type.model == 'mainoeuvre':
            try:
                return MainOeuvre.objects.get(id=obj.element_id).unite
            except MainOeuvre.DoesNotExist:
                return "h"  # Default for labor
        return None
    
    def get_element_prix(self, obj):
        """
        Récupère le prix unitaire de l'élément (fourniture ou main d'œuvre).
        """
        if obj.element_type.model == 'fourniture':
            try:
                return Fourniture.objects.get(id=obj.element_id).prix_achat_ht
            except Fourniture.DoesNotExist:
                return None
        elif obj.element_type.model == 'mainoeuvre':
            try:
                return MainOeuvre.objects.get(id=obj.element_id).cout_horaire
            except MainOeuvre.DoesNotExist:
                return None
        return None
    
    def get_element_type_nom(self, obj):
        """
        Récupère le nom du type d'élément (fourniture ou main d'œuvre).
        """
        return obj.element_type.model

class IngredientOuvrageCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création et la mise à jour d'un IngredientOuvrage.
    """
    element_type_nom = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = IngredientOuvrage
        fields = ['ouvrage', 'element_type_nom', 'element_id', 'quantite', 'waste_allowance', 'notes']
    
    def validate(self, data):
        """
        Valide les données et convertit element_type_nom en element_type.
        """
        # Pour les mises à jour, nous n'avons pas besoin de tous les champs
        is_update = self.instance is not None
        
        # Si c'est une mise à jour et que element_type_nom n'est pas fourni,
        # nous utilisons la valeur existante
        if is_update and 'element_type_nom' not in data:
            # Nous ne modifions pas le type d'élément, juste la quantité
            return data
            
        element_type_nom = data.pop('element_type_nom', None)
        if not element_type_nom and not is_update:
            raise serializers.ValidationError(
                {"element_type_nom": "Ce champ est obligatoire pour la création"}
            )
            
        if element_type_nom and element_type_nom not in ['fourniture', 'mainoeuvre']:
            raise serializers.ValidationError(
                {"element_type_nom": f"Valeur '{element_type_nom}' invalide. Doit être 'fourniture' ou 'mainoeuvre'"}
            )
        
        # Si nous avons un element_type_nom, nous récupérons le ContentType correspondant
        if element_type_nom:
            from django.contrib.contenttypes.models import ContentType
            
            if element_type_nom == 'fourniture':
                model_class = Fourniture
            else:  # element_type_nom == 'mainoeuvre'
                model_class = MainOeuvre
                
            try:
                # Obtenir le ContentType à partir de la classe de modèle
                content_type = ContentType.objects.get_for_model(model_class)
                data['element_type'] = content_type
            except Exception as e:
                raise serializers.ValidationError(
                    {"element_type_nom": f"Impossible de trouver le ContentType pour '{element_type_nom}': {str(e)}"}
                )
        
        # Vérifie que l'élément existe, mais seulement si element_id est fourni
        # ou si c'est une création
        element_id = data.get('element_id')
        if not element_id and not is_update:
            raise serializers.ValidationError(
                {"element_id": "Ce champ est obligatoire pour la création"}
            )
            
        # Si nous avons à la fois element_type_nom et element_id, nous vérifions que l'élément existe
        if element_type_nom and element_id:
            if element_type_nom == 'fourniture':
                try:
                    Fourniture.objects.get(id=element_id)
                except Fourniture.DoesNotExist:
                    available_ids = list(Fourniture.objects.values_list('id', flat=True))
                    raise serializers.ValidationError(
                        {"element_id": f"Fourniture avec id={element_id} non trouvée. IDs disponibles: {available_ids}"}
                    )
            elif element_type_nom == 'mainoeuvre':
                try:
                    MainOeuvre.objects.get(id=element_id)
                except MainOeuvre.DoesNotExist:
                    available_ids = list(MainOeuvre.objects.values_list('id', flat=True))
                    raise serializers.ValidationError(
                        {"element_id": f"MainOeuvre avec id={element_id} non trouvée. IDs disponibles: {available_ids}"}
                    )
        
        return data
    
    def update(self, instance, validated_data):
        """
        Méthode personnalisée pour la mise à jour, qui ne modifie que les champs fournis.
        """
        # Nous ne mettons à jour que les champs fournis
        for field in ['quantite', 'waste_allowance', 'notes']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance

class OuvrageSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle Ouvrage.
    """
    categorie_nom = serializers.SerializerMethodField(read_only=True)
    debourse_sec = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    totalCost = serializers.DecimalField(source='debourse_sec', max_digits=12, decimal_places=2, read_only=True)
    recommendedPrice = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margin = serializers.DecimalField(source='marge', max_digits=5, decimal_places=2, read_only=True)
    laborCost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    materialCost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Ouvrage
        fields = [
            'id', 'nom', 'unite', 'categorie', 'categorie_nom', 'description', 'code', 
            'prix_recommande', 'marge', 'is_custom', 'type', 'complexity', 'efficiency',
            'duration_estimate', 'requires_certification', 'debourse_sec', 'totalCost',
            'recommendedPrice', 'margin', 'laborCost', 'materialCost', 'created_at', 'updated_at'
        ]
    
    def get_categorie_nom(self, obj):
        """
        Récupère le nom de la catégorie associée à l'ouvrage.
        """
        if obj.categorie:
            return obj.categorie.chemin_complet
        return None

class OuvrageDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour le modèle Ouvrage, incluant ses ingrédients.
    """
    categorie_details = CategorieSerializer(source='categorie', read_only=True)
    ingredients = IngredientOuvrageSerializer(many=True, read_only=True)
    debourse_sec = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    totalCost = serializers.DecimalField(source='debourse_sec', max_digits=12, decimal_places=2, read_only=True)
    recommendedPrice = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margin = serializers.DecimalField(source='marge', max_digits=5, decimal_places=2, read_only=True)
    laborCost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    materialCost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Ouvrage
        fields = [
            'id', 'nom', 'unite', 'categorie', 'categorie_details', 'description', 'code', 
            'prix_recommande', 'marge', 'is_custom', 'type', 'complexity', 'efficiency',
            'duration_estimate', 'requires_certification', 'debourse_sec', 'totalCost',
            'recommendedPrice', 'margin', 'laborCost', 'materialCost', 'ingredients',
            'created_at', 'updated_at'
        ]

# Sérialiseurs simplifiés pour l'intégration frontend
class LibraryItemSerializer(serializers.Serializer):
    """
    Sérialiseur unifié pour tous les éléments de la bibliothèque (fournitures, main d'œuvre, ouvrages).
    Utilisé pour l'intégration avec le formulaire de devis.
    """
    id = serializers.IntegerField()
    nom = serializers.CharField()
    type = serializers.CharField()
    unite = serializers.CharField()
    unitPrice = serializers.DecimalField(max_digits=12, decimal_places=2)
    categorie = serializers.CharField(source='categorie.nom', allow_null=True)
    description = serializers.CharField(allow_null=True)
    code = serializers.CharField(allow_null=True)
    
    # Champs spécifiques aux fournitures
    vatRate = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    wasteFactor = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    supplier = serializers.CharField(required=False, allow_null=True)
    
    # Champs spécifiques à la main d'œuvre
    skill_level = serializers.CharField(required=False, allow_null=True)
    productivity_factor = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    
    # Champs spécifiques aux ouvrages
    complexity = serializers.CharField(required=False, allow_null=True)
    efficiency = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    duration_estimate = serializers.DecimalField(max_digits=8, decimal_places=2, required=False, allow_null=True)
    requires_certification = serializers.BooleanField(required=False, allow_null=True)