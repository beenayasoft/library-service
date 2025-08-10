# Generated migration for supplier CRM integration
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fourniture',
            name='supplier',
            field=models.CharField(
                blank=True, 
                max_length=100, 
                null=True, 
                verbose_name='Fournisseur (legacy)',
                help_text='Champ legacy - préférer supplier_id pour nouveaux matériaux'
            ),
        ),
        migrations.AddField(
            model_name='fourniture',
            name='supplier_id',
            field=models.UUIDField(
                blank=True, 
                null=True, 
                verbose_name='Fournisseur CRM',
                help_text='Référence vers le fournisseur dans le service CRM',
                db_index=True
            ),
        ),
    ]