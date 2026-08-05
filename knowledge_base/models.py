from django.db import models
from django.conf import settings


class Article(models.Model):

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published'),
        ('ARCHIVED', 'Archived'),
    )

    CATEGORY_CHOICES = [

        ("Hardware Issue", "Hardware Issue"),
        ("Software Issue", "Software Issue"),
        ("Network Issue", "Network Issue"),
        ("Email / Outlook", "Email / Outlook"),

        ("New Employee Onboarding", "New Employee Onboarding"),
        ("Leave Policy", "Leave Policy"),
        ("Payroll Inquiry", "Payroll Inquiry"),

        ("Office Supplies", "Office Supplies"),
        ("Facility Request", "Facility Request"),

        ("Invoice Processing", "Invoice Processing"),
        ("Budget Approval", "Budget Approval"),

        ("Laptop Request", "Laptop Request"),
        ("Software License", "Software License"),

        ("Account Creation", "Account Creation"),
        ("Permission Request", "Permission Request"),
        ("VPN Access", "VPN Access"),

        ("General Inquiry", "General Inquiry"),

    ]

    title = models.CharField(max_length=255)

    summary = models.TextField(blank=True)

    content = models.TextField()

    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kb_articles'
    )

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='kb_articles'
    )

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )

    is_internal = models.BooleanField(default=False)

    tags = models.CharField(max_length=255, blank=True)

    views_count = models.PositiveIntegerField(default=0)

    helpful_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kb_articles_created'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):

        if not self.tenant_id and self.created_by_id:
            self.tenant_id = self.created_by.tenant_id

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]