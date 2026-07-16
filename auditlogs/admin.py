from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_label', 'module', 'severity', 'target', 'actor', 'created_at')
    list_filter = ('module', 'severity')
    search_fields = ('action_label', 'target', 'action')
    ordering = ('-created_at',)
