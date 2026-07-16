from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='departments'
    )


    sla_critical = models.PositiveIntegerField(default=2)
    sla_high = models.PositiveIntegerField(default=8)
    sla_medium = models.PositiveIntegerField(default=24)
    sla_low = models.PositiveIntegerField(default=72)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name