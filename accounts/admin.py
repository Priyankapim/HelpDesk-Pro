
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'email',
        'username',
        'role',
        'department',
        'is_staff',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'Additional Info',
            {
                'fields': (
                    'role',
                    'department',
                    'phone',
                    'profile_image',
                )
            },
        ),
    )