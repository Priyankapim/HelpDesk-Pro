import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configuration', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [

        migrations.AlterField(
            model_name='workinghours',
            name='day',
            field=models.CharField(
                choices=[
                    ('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'),
                    ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'),
                    ('SUN', 'Sunday'),
                ],
                max_length=3,
            ),
        ),

        migrations.AddField(
            model_name='workinghours',
            name='tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='working_hours', to='tenants.tenant',
            ),
        ),

        migrations.AlterUniqueTogether(
            name='workinghours',
            unique_together={('tenant', 'day')},
        ),

        migrations.AddField(
            model_name='holiday',
            name='tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='holidays', to='tenants.tenant',
            ),
        ),

        migrations.AddField(
            model_name='escalationrule',
            name='tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='escalation_rules', to='tenants.tenant',
            ),
        ),

        migrations.AddField(
            model_name='emailtemplate',
            name='tenant',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='email_templates', to='tenants.tenant',
            ),
        ),

    ]