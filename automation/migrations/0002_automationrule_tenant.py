import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('automation', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='automationrule',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='automation_rules',
                to='tenants.tenant',
            ),
        ),
    ]