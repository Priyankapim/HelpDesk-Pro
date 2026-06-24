from django import forms
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):

    class Meta:

        model = Ticket

        fields = [
            "title",
            "description",
            "department",
            "priority",
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

            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "priority": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = TicketComment

        fields = ['comment']