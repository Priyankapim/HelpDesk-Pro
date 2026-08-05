from django.db import models
from django.conf import settings


class AutomationRule(models.Model):

    TRIGGER_CHOICES = (
        ('TICKET_CREATED', 'Ticket Created'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('PRIORITY_CHANGED', 'Priority Changed'),
        ('TICKET_ASSIGNED', 'Ticket Assigned'),
        ('UNASSIGNED_TOO_LONG', 'Unassigned Too Long'),
        ('SLA_BREACH', 'SLA Breach'),
        ('COMMENT_ADDED', 'Comment Added'),
    )

    TRIGGER_DESCRIPTIONS = {
        'TICKET_CREATED': 'When a new ticket is submitted',
        'STATUS_CHANGED': "When a ticket's status is updated",
        'PRIORITY_CHANGED': "When a ticket's priority changes",
        'TICKET_ASSIGNED': 'When a ticket is assigned to an agent',
        'UNASSIGNED_TOO_LONG': 'When a ticket stays unassigned for hours',
        'SLA_BREACH': "When a ticket's SLA deadline is breached",
        'COMMENT_ADDED': 'When someone comments on a ticket',
    }

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    trigger = models.CharField(
        max_length=30,
        choices=TRIGGER_CHOICES
    )

    is_active = models.BooleanField(default=True)
    execution_count = models.PositiveIntegerField(default=0)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='automation_rules'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RuleCondition(models.Model):

    FIELD_CHOICES = (
        ('priority', 'Priority'),
        ('status', 'Status'),
        ('department_id', 'Department ID'),
        ('assignee', 'Assignee'),
    )

    OPERATOR_CHOICES = (
        ('equals', 'equals'),
        ('not_equals', 'does not equal'),
        ('contains', 'contains'),
        ('not_contains', 'does not contain'),
        ('is_empty', 'is empty'),
        ('is_not_empty', 'is not empty'),
    )

    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.CASCADE,
        related_name='conditions'
    )

    field = models.CharField(
        max_length=30,
        choices=FIELD_CHOICES,
        default='priority'
    )

    operator = models.CharField(
        max_length=20,
        choices=OPERATOR_CHOICES,
        default='equals'
    )

    value = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f"{self.field} {self.operator} {self.value}"


class RuleAction(models.Model):

    ACTION_CHOICES = (
        ('assign_agent', 'Assign to Agent'),
        ('change_priority', 'Change Priority'),
        ('change_status', 'Change Status'),
        ('add_tag', 'Add Tag'),
        ('send_notification', 'Send Notification'),
        ('send_email_notification', 'Send Email Notification'),
    )

    rule = models.ForeignKey(
        AutomationRule,
        on_delete=models.CASCADE,
        related_name='actions'
    )

    action_type = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        default='send_notification'
    )

    value = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.action_type}: {self.value}"