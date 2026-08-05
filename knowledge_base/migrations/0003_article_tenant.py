import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_base', '0002_category_to_charfield'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='kb_articles',
                to='tenants.tenant',
            ),
        ),
    ]