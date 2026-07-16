import re
from .models import User
from django import forms
from .models import Invitation


class ChangePasswordForm(forms.Form):

    current_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Current Password"
            }
        )
    )

    new_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "New Password"
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password"
            }
        )
    )





class UserCreationAdminForm(forms.ModelForm):

    class Meta:

        model = User

        fields = (
            "first_name",
            "last_name",
            "email",
            "username",
            "role",
            "department",
            "phone",
            "is_active",
            "is_staff",
        )








class InvitationForm(forms.ModelForm):

    class Meta:

        model = Invitation

        fields = [

            "first_name",
            "last_name",
            "email",
            "role",
            "department",

        ]

        widgets = {

            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "John"
            }),

            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Doe"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "user@company.com"
            }),

            "role": forms.Select(attrs={
                "class": "form-select"
            }),

            "department": forms.Select(attrs={
                "class": "form-select"
            }),

        }





class AcceptInvitationForm(forms.Form):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Create Password"
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm Password"
            }
        )
    )

    def clean_password(self):

        password = self.cleaned_data["password"]

        if len(password) < 8:
            raise forms.ValidationError(
                "Password must be at least 8 characters."
            )

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Password must contain one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise forms.ValidationError(
                "Password must contain one lowercase letter."
            )

        if not re.search(r"\d", password):
            raise forms.ValidationError(
                "Password must contain one number."
            )

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise forms.ValidationError(
                "Password must contain one special character."
            )

        return password