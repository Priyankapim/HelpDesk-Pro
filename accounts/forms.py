from django import forms
from .models import User

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