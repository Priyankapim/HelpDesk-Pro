from django.db import models
from django.conf import settings
from departments.models import Department
from django.utils import timezone
from datetime import timedelta


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Ticket(models.Model):
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

    AFFECTED_SYSTEM_CHOICES = [

        ("Laptop", "Laptop"),
        ("Desktop", "Desktop"),
        ("Printer", "Printer"),
        ("Windows", "Windows"),
        ("Office 365", "Office 365"),
        ("Outlook", "Outlook"),
        ("Email", "Email"),
        ("Network", "Network"),
        ("VPN", "VPN"),
        ("Authentication", "Authentication"),
        ("Active Directory", "Active Directory"),
        ("HRMS", "HRMS"),
        ("Payroll", "Payroll"),
        ("Hardware", "Hardware"),
        ("Software", "Software"),
        ("Database", "Database"),
        ("Website", "Website"),
        ("Other", "Other"),

    ]

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),

    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Pending User', 'Pending User'),
        ('Escalated', 'Escalated'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
        ('Reopened', 'Reopened'),
    ]

    ticket_number = models.CharField(
        max_length=20,
        unique=True
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField()

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Low'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_tickets'
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    category = models.CharField(
        max_length=100,
        default="General Inquiry"
    )

    affected_system = models.CharField(
        max_length=100,
        choices=AFFECTED_SYSTEM_CHOICES,
        default="Other"
    )

    tags = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tickets'
    )

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last_ticket = Ticket.objects.count() + 1
            self.ticket_number = f"TKT-{last_ticket:04d}"

        if not self.tenant_id and self.created_by_id:
            self.tenant_id = self.created_by.tenant_id

        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number

    @property
    def sla_deadline(self):

        if self.priority == "Critical":
            hours = 8

        elif self.priority == "High":
            hours = 24

        elif self.priority == "Medium":
            hours = 48

        else:
            hours = 72

        return self.created_at + timedelta(hours=hours)

    @property
    def sla_status(self):

        diff = self.sla_deadline - timezone.now()
        if diff.total_seconds() < 0:
            overdue = abs(diff)
            days = overdue.days
            hours = overdue.seconds // 3600

            return {
                "text": f"{days}d {hours}h overdue",
                "class": "danger"
            }

        else:
            days = diff.days
            hours = diff.seconds // 3600

            return {
                "text": f"{days}d {hours}h left",
                "class": "success"
            }

class TicketComment(models.Model):

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user} - {self.ticket}"


class Notification(models.Model):
        user = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="notifications"
        )

        ticket = models.ForeignKey(
            "Ticket",
            on_delete=models.CASCADE,
            related_name="notifications"
        )

        title = models.CharField(
            max_length=100
        )

        message = models.CharField(
            max_length=255
        )

        is_read = models.BooleanField(
            default=False
        )

        created_at = models.DateTimeField(
            auto_now_add=True
        )

        class Meta:
            ordering = ["-created_at"]

        def __str__(self):
            return self.title




