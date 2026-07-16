import re

from django import forms


class AcceptInviteForm(forms.Form):

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
