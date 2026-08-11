import random
import string

from django.conf import settings
from django.db import models

from tenants.models import Tenant


def generate_ticket_number():
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
    return f"SAAS-{suffix}"


class SupportRequest(models.Model):

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING_USER', 'Pending User'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    )

    ticket_number = models.CharField(max_length=20, unique=True, default=generate_ticket_number, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='support_requests')

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_requests'
    )

    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='raised_support_requests'
    )

    subject = models.CharField(max_length=255)
    description = models.TextField()

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.subject}"


class SupportMessage(models.Model):

    request = models.ForeignKey(SupportRequest, on_delete=models.CASCADE, related_name='messages')

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_messages'
    )

    # True if a NabiTech (SUPER_ADMIN) staff member wrote this reply,
    # False if it came from the tenant side.
    is_staff_reply = models.BooleanField(default=False)

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message on {self.request.ticket_number}"
