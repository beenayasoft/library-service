from django.core.management.base import BaseCommand, CommandError
from tenant_schema.models import Client, Domain

class Command(BaseCommand):
    help = 'Crée un nouveau tenant avec son domaine associé'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Nom du tenant')
        parser.add_argument('domain', type=str, help='Domaine du tenant (ex: client1.localhost)')
        parser.add_argument('--description', type=str, help='Description du tenant', default='')
        parser.add_argument('--company-type', type=str, 
                          choices=['general_contractor', 'specialty_contractor', 'architect', 
                                 'engineer', 'developer', 'other'],
                          default='general_contractor',
                          help='Type d\'entreprise')
        parser.add_argument('--email', type=str, help='Email de contact', default='')
        parser.add_argument('--phone', type=str, help='Téléphone', default='')
        parser.add_argument('--max-users', type=int, help='Nombre max d\'utilisateurs', default=10)
        parser.add_argument('--storage-limit', type=int, help='Limite de stockage en GB', default=5)

    def handle(self, *args, **options):
        name = options['name']
        domain = options['domain']
        
        # Vérifier si le tenant existe déjà
        if Client.objects.filter(name=name).exists():
            raise CommandError(f'Le tenant "{name}" existe déjà.')
        
        # Vérifier si le domaine existe déjà
        if Domain.objects.filter(domain=domain).exists():
            raise CommandError(f'Le domaine "{domain}" existe déjà.')
        
        try:
            # Créer le tenant
            tenant = Client.objects.create(
                name=name,
                description=options['description'],
                company_type=options['company_type'],
                contact_email=options['email'],
                contact_phone=options['phone'],
                max_users=options['max_users'],
                storage_limit_gb=options['storage_limit']
            )
            
            # Créer le domaine principal
            domain_obj = Domain.objects.create(
                domain=domain,
                tenant=tenant,
                is_primary=True,
                description=f'Domaine principal pour {name}'
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Tenant "{name}" créé avec succès!\n'
                    f'Schema: {tenant.schema_name}\n'
                    f'Domaine: {domain}\n'
                    f'Type: {tenant.get_company_type_display()}'
                )
            )
            
            self.stdout.write(
                self.style.WARNING(
                    'N\'oubliez pas de lancer les migrations pour ce tenant:\n'
                    f'python manage.py migrate_schemas --tenant {tenant.schema_name}'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Erreur lors de la création du tenant: {str(e)}')