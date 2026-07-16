from django.contrib import admin

from .models import WorkingHours, Holiday, EscalationRule, EmailTemplate

admin.site.register(WorkingHours)
admin.site.register(Holiday)
admin.site.register(EscalationRule)
admin.site.register(EmailTemplate)
