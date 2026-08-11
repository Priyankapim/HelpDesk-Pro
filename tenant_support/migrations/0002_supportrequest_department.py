from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('departments', '0005_seed_categories'),
        ('tenant_support', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='supportrequest',
            name='department',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='support_requests',
                to='departments.department',
            ),
        ),
    ]