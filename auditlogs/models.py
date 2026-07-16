import json

from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    MODULE_CHOICES = (
        ('USERS', 'Users'),
        ('ROLES', 'Roles'),
        ('TICKETS', 'Tickets'),
        ('DEPARTMENTS', 'Departments'),
        ('CONFIG', 'Config'),
        ('SYSTEM', 'System'),
        ('KNOWLEDGE_BASE', 'Knowledge Base'),
        ('TENANTS', 'Tenants'),
        ('INVITES', 'Invites'),
        ('SUPPORT', 'Support'),
    )

    SEVERITY_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('CRITICAL', 'Critical'),
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )

    action = models.CharField(
        max_length=100
    )

    action_label = models.CharField(
        max_length=150
    )

    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        default='SYSTEM'
    )

    target = models.CharField(
        max_length=255,
        blank=True
    )

    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='INFO'
    )

    changes_before = models.JSONField(
        null=True,
        blank=True
    )

    changes_after = models.JSONField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action_label} - {self.target}"

    @property
    def actor_name(self):
        if self.actor:
            full_name = f"{self.actor.first_name} {self.actor.last_name}".strip()
            return full_name if full_name else self.actor.email
        return "System"

    @property
    def changes_summary(self):
        """Short preview shown in the table's CHANGES column, e.g. 'role: end_user'."""
        data = self.changes_after or self.changes_before

        if not data:
            return None

        key, value = next(iter(data.items()))
        text = f"{key}: {value}"

        if len(text) > 22:
            text = text[:22] + "…"

        return text

    @property
    def changes_before_json(self):
        return json.dumps(self.changes_before) if self.changes_before else 'null'

    @property
    def changes_after_json(self):
        return json.dumps(self.changes_after) if self.changes_after else 'null'
