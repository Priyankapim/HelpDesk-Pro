from django.db import models

from departments.models import Department


class WorkingHours(models.Model):

    DAY_CHOICES = (
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
        ('SUN', 'Sunday'),
    )

    day = models.CharField(max_length=3, choices=DAY_CHOICES, unique=True)
    is_working = models.BooleanField(default=True)
    start_time = models.TimeField(default='09:00')
    end_time = models.TimeField(default='17:00')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.get_day_display()


class Holiday(models.Model):

    name = models.CharField(max_length=150)
    date = models.DateField()
    recurring = models.BooleanField(default=False)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.name


class EscalationRule(models.Model):

    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='escalation_rules'
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    escalate_after_hours = models.PositiveIntegerField()
    notify_email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.department.name} - {self.get_priority_display()}"


class EmailTemplate(models.Model):

    TRIGGER_CHOICES = (
        ('TICKET_CREATED', 'Ticket Created'),
        ('TICKET_ASSIGNED', 'Ticket Assigned'),
        ('TICKET_RESOLVED', 'Ticket Resolved'),
        ('TICKET_ESCALATED', 'Ticket Escalated'),
        ('SLA_WARNING', 'SLA Warning'),
        ('CSAT_REQUEST', 'CSAT Request'),
    )

    name = models.CharField(max_length=150)
    trigger_event = models.CharField(max_length=20, choices=TRIGGER_CHOICES)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
