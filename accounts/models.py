from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import timedelta
from django.utils import timezone

class User(AbstractUser):

    ROLE_CHOICES = (
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),
        ('AGENT', 'Agent'),
        ('EMPLOYEE', 'Employee'),
    )

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='EMPLOYEE'
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True
    )

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users'
    )

    is_locked = models.BooleanField(
        default=False
    )

    failed_login_attempts = models.PositiveIntegerField(
        default=0
    )

    locked_at = models.DateTimeField(
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

import uuid

class Invitation(models.Model):

    STATUS_CHOICES = (

        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("EXPIRED", "Expired"),
        ("REVOKED", "Revoked"),

    )

    email = models.EmailField()

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100,
        blank=True
    )

    role = models.CharField(
        max_length=20,
        choices=User.ROLE_CHOICES
    )

    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = (
                    timezone.now() + timedelta(days=7)
            )

        super().save(*args, **kwargs)


class SecuritySettings(models.Model):
    """
    Single-row table holding site-wide account lockout policy.
    Editable only by Admin/Super Admin from the Security Settings page.
    """

    max_failed_attempts = models.PositiveIntegerField(default=5)
    lockout_duration_minutes = models.PositiveIntegerField(default=15)

    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Security Settings"


class LoginActivity(models.Model):

    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('LOCKED', 'Locked'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_activities'
    )

    email_attempted = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_attempted} - {self.status}"


class UserSession(models.Model):
    """
    Tracks metadata (IP/device) for each login so 'Active Sessions'
    can show real device info, not just the raw Django session table.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_sessions'
    )

    session_key = models.CharField(max_length=40, unique=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.email} - {self.session_key[:8]}"