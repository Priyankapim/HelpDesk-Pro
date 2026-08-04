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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        from departments.models import Department

        queryset = Department.objects.filter(is_active=True)

        if user and user.tenant_id:
            queryset = queryset.filter(tenant_id=user.tenant_id)

        if self.instance and self.instance.pk and self.instance.department_id:
            queryset = Department.objects.filter(
                models.Q(pk=self.instance.department_id) |
                (models.Q(is_active=True) & (models.Q(tenant_id=user.tenant_id) if user and user.tenant_id else models.Q()))
            )

        self.fields["department"].queryset = queryset


class CommentForm(forms.ModelForm):

    class Meta:
        model = TicketComment

        fields = ['comment']