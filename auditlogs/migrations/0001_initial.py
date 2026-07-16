# Generated manually to match Django 6.0.5 migration conventions

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=100)),
                ('action_label', models.CharField(max_length=150)),
                ('module', models.CharField(choices=[('USERS', 'Users'), ('ROLES', 'Roles'), ('TICKETS', 'Tickets'), ('DEPARTMENTS', 'Departments'), ('CONFIG', 'Config'), ('SYSTEM', 'System')], default='SYSTEM', max_length=20)),
                ('target', models.CharField(blank=True, max_length=255)),
                ('severity', models.CharField(choices=[('INFO', 'Info'), ('WARNING', 'Warning'), ('CRITICAL', 'Critical')], default='INFO', max_length=10)),
                ('changes_before', models.JSONField(blank=True, null=True)),
                ('changes_after', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
