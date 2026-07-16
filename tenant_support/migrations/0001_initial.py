import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import tenant_support.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SupportRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_number', models.CharField(default=tenant_support.models.generate_ticket_number, editable=False, max_length=20, unique=True)),
                ('subject', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], default='MEDIUM', max_length=10)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('PENDING_USER', 'Pending User'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], default='OPEN', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('raised_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='raised_support_requests', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='support_requests', to='tenants.tenant')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SupportMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_staff_reply', models.BooleanField(default=False)),
                ('message', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='support_messages', to=settings.AUTH_USER_MODEL)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='tenant_support.supportrequest')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
