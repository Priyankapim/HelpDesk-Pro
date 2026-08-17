from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import uuid


class Tenant(models.Model):

    PLAN_CHOICES = (
        ('TRIAL', 'Trial'),
        ('STARTER', 'Starter'),
        ('PROFESSIONAL', 'Professional'),
        ('ENTERPRISE', 'Enterprise'),
    )

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='TRIAL')
    is_active = models.BooleanField(default=True)

    max_users = models.PositiveIntegerField(null=True, blank=True)  # null = unlimited
    notes = models.TextField(blank=True)

    trial_ends_at = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def total_users(self):
        return self.users.count()

    @property
    def total_tickets(self):
        return self.support_requests.count()

    @property
    def onboarding_percent(self):
        steps = self.onboarding_steps
        done = len([s for s in steps if s['done']])
        return int((done / len(steps)) * 100)

    @property
    def onboarding_steps(self):
        has_admin = self.users.filter(role='ADMIN').exists()
        invite_count = self.invites.count()

        return [
            {
                "title": "1. NabiTech Creates Tenant",
                "description": "Super admin creates the tenant org (e.g. this organization) and sets plan limits.",
                "done": True,
            },
            {
                "title": "2. Invite Tenant Admin",
                "description": "Super admin invites the tenant admin via email. They receive an invite link.",
                "done": invite_count > 0,
            },
            {
                "title": "3. Admin Signs In",
                "description": "The tenant admin clicks the invite email, signs in, and is auto-assigned the 'admin' role.",
                "done": has_admin,
            },
            {
                "title": "4. Admin Invites Team",
                "description": "The tenant admin logs into the Users admin panel and invites their employees.",
                "done": invite_count > 1,
            },
            {
                "title": "5. Users Raise Tickets",
                "description": "Employees sign in and use the Self-Service Portal to raise support tickets.",
                "done": self.users.count() > 1,
            },
            {
                "title": "6. Agents Resolve",
                "description": "Tenant agents see only their tenant's ticket queue. Super admins can see all tenants.",
                "done": False,
            },
        ]


class Invite(models.Model):

    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('AGENT', 'Agent'),
        ('EMPLOYEE', 'End User'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('EXPIRED', 'Expired'),
        ('REVOKED', 'Revoked'),
    )

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invites')

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    name = models.CharField(max_length=150)
    email = models.EmailField()

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='EMPLOYEE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invites'
    )

    expires_at = models.DateField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}>"

    @property
    def is_expired(self):
        return self.status == 'PENDING' and self.expires_at < timezone.now().date()

    @property
    def display_status(self):
        if self.is_expired:
            return 'EXPIRED'
        return self.status
