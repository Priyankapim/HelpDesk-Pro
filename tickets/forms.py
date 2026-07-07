from django import forms
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):

    class Meta:

        model = Ticket

        fields = [
            "title",
            "description",
            "department",
            "category",
            "priority",
            "affected_system",
            "tags",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter ticket title",
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": "Describe your issue",
                }
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_department",
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-select",
                    "id": "id_category",
                }
            ),



            "affected_system": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "laptop, windows, printer",
                }
            ),

        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = TicketComment

        fields = ['comment']