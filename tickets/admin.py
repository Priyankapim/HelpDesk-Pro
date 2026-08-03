from django.contrib import admin
from .models import Ticket, TicketComment,  Notification


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "title", "created_by", "tenant", "department", "status", "priority", "created_at")
    list_filter = ("tenant", "department", "status", "priority")
    search_fields = ("ticket_number", "title", "created_by__email", "created_by__username")


admin.site.register(TicketComment)
admin.site.register(Notification)
