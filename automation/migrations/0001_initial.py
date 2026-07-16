import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutomationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('trigger', models.CharField(choices=[('TICKET_CREATED', 'Ticket Created'), ('STATUS_CHANGED', 'Status Changed'), ('PRIORITY_CHANGED', 'Priority Changed'), ('TICKET_ASSIGNED', 'Ticket Assigned'), ('UNASSIGNED_TOO_LONG', 'Unassigned Too Long'), ('SLA_BREACH', 'SLA Breach'), ('COMMENT_ADDED', 'Comment Added')], max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('execution_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RuleAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('assign_agent', 'Assign to Agent'), ('change_priority', 'Change Priority'), ('change_status', 'Change Status'), ('add_tag', 'Add Tag'), ('send_notification', 'Send Notification'), ('send_email_notification', 'Send Email Notification')], default='send_notification', max_length=30)),
                ('value', models.CharField(blank=True, max_length=255)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='automation.automationrule')),
            ],
        ),
        migrations.CreateModel(
            name='RuleCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(choices=[('priority', 'Priority'), ('status', 'Status'), ('department_id', 'Department ID'), ('assignee', 'Assignee')], default='priority', max_length=30)),
                ('operator', models.CharField(choices=[('equals', 'equals'), ('not_equals', 'does not equal'), ('contains', 'contains'), ('not_contains', 'does not contain'), ('is_empty', 'is empty'), ('is_not_empty', 'is not empty')], default='equals', max_length=20)),
                ('value', models.CharField(blank=True, max_length=150)),
                ('rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='automation.automationrule')),
            ],
        ),
    ]