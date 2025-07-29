import uuid
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

class Client(TenantMixin):
    """
    Modèle tenant simplifié pour django-tenants - Library Service
    Aligné avec l'architecture SOA et les autres services (CRM, Document)
    """
    # Champs essentiels
    name = models.CharField(max_length=100, verbose_name="Nom du client")
    tenant_uuid = models.UUIDField(
        unique=True,
        null=True,
        blank=True, 
        verbose_name="UUID du tenant",
        help_text="UUID fourni par le service tenant"
    )
    
    # Métadonnées de base
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")
    
    # Configuration minimale
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    max_library_items = models.IntegerField(
        default=10000, 
        verbose_name="Nombre maximum d'éléments de bibliothèque"
    )
    
    # Configuration automatique du schéma
    auto_create_schema = True
    auto_drop_schema = False  # Sécurité : ne pas supprimer automatiquement
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        indexes = [
            models.Index(fields=['tenant_uuid']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.schema_name})"

class Domain(DomainMixin):
    """
    Modèle domaine simplifié pour django-tenants - Library Service
    Aligné avec l'architecture SOA (minimal comme CRM/Document services)
    """
    class Meta:
        verbose_name = "Domaine"
        verbose_name_plural = "Domaines"
    
    def __str__(self):
        return f"{self.domain} -> {self.tenant.name}"
