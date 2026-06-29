from django.contrib import admin
from .models import Ticket, TicketComment,  Notification

admin.site.register(Ticket)
admin.site.register(TicketComment)
admin.site.register(Notification)

