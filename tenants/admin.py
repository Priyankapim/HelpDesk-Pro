from django.contrib import admin

from .models import Tenant, Invite


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'plan', 'is_active', 'created_at')
    list_filter = ('plan', 'is_active')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'tenant', 'role', 'status', 'expires_at')
    list_filter = ('status', 'role', 'tenant')
    search_fields = ('name', 'email')
