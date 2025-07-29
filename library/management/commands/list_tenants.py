from django.core.management.base import BaseCommand
from django.utils import timezone
from tenant_schema.models import Client, Domain

class Command(BaseCommand):
    help = 'Liste tous les tenants avec leurs informations'

    def add_arguments(self, parser):
        parser.add_argument('--active-only', action='store_true', 
                          help='Afficher seulement les tenants actifs')
        parser.add_argument('--with-domains', action='store_true',
                          help='Afficher les domaines associés')

    def handle(self, *args, **options):
        tenants = Client.objects.all()
        
        if options['active_only']:
            tenants = tenants.filter(is_active=True)
        
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('Aucun tenant trouvé.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Tenants trouvés: {tenants.count()}'))
        self.stdout.write('=' * 80)
        
        for tenant in tenants:
            status = "✓ Actif" if tenant.is_active else "✗ Inactif"
            
            self.stdout.write(f'Nom: {tenant.name}')
            self.stdout.write(f'Schema: {tenant.schema_name}')
            self.stdout.write(f'Status: {status}')
            self.stdout.write(f'Type: {tenant.get_company_type_display()}')
            self.stdout.write(f'Email: {tenant.contact_email or "Non défini"}')
            self.stdout.write(f'Max utilisateurs: {tenant.max_users}')
            self.stdout.write(f'Limite stockage: {tenant.storage_limit_gb} GB')
            self.stdout.write(f'Créé le: {tenant.created_at.strftime("%d/%m/%Y %H:%M")}')
            
            if options['with_domains']:
                domains = Domain.objects.filter(tenant=tenant)
                if domains.exists():
                    self.stdout.write('Domaines:')
                    for domain in domains:
                        primary = " (principal)" if domain.is_primary else ""
                        self.stdout.write(f'  - {domain.domain}{primary}')
                else:
                    self.stdout.write('Domaines: Aucun')
            
            if tenant.description:
                self.stdout.write(f'Description: {tenant.description}')
            
            self.stdout.write('-' * 40)