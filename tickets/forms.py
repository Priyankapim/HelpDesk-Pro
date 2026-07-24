from django import forms
from django.db import models
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):

    category = forms.CharField(
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_category",
            }
        )
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from departments.models import Department

        queryset = Department.objects.filter(is_active=True)

        if self.instance and self.instance.pk and self.instance.department_id:
            queryset = Department.objects.filter(
                models.Q(is_active=True) | models.Q(pk=self.instance.department_id)
            )

        self.fields["department"].queryset = queryset


class CommentForm(forms.ModelForm):

    class Meta:
        model = TicketComment

        fields = ['comment']