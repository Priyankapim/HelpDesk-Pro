
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .utils import generate_password, send_welcome_email, generate_username
from .forms import UserCreationAdminForm




@admin.register(User)
class CustomUserAdmin(UserAdmin):

    add_form = UserCreationAdminForm

    add_fieldsets = (

        (

            None,

            {

                "classes": ("wide",),

                "fields": (

                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "phone",

                ),

            },

        ),

    )

    list_display = (

        "email",
        "username",
        "role",
        "is_staff",


    )

    fieldsets = UserAdmin.fieldsets + (

        (

            "Additional Info",

            {

                "fields": (

                    "role",
                    "department",
                    "phone",
                    "profile_image",

                )

            },

        ),

    )

    def save_model(self, request, obj, form, change):

        if not change:

            obj.is_active = True

            if obj.role == "SUPER_ADMIN":
                obj.is_staff = True
            else:
                obj.is_staff = False

            # Auto Username
            obj.username = generate_username(obj.email)

            # Auto Password
            password = generate_password()

            obj.set_password(password)

            super().save_model(
                request,
                obj,
                form,
                change
            )

            send_welcome_email(
                obj,
                password
            )

        else:

            super().save_model(
                request,
                obj,
                form,
                change
            )