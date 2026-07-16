from django.contrib import admin

from .models import SupportRequest, SupportMessage


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ('ticket_number', 'subject', 'tenant', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'tenant')
    search_fields = ('ticket_number', 'subject')
    inlines = [SupportMessageInline]
