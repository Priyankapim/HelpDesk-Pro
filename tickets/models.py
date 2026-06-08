from django.db import models
from django.conf import settings
from departments.models import Department


class Ticket(models.Model):

    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
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

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            last_ticket = Ticket.objects.count() + 1

            self.ticket_number = f"TKT-{last_ticket:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.ticket_number

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

    