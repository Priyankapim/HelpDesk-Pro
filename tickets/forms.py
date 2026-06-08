from django import forms
from .models import Ticket, TicketComment


class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket

        fields = [
            'title',
            'description',
            'department',
            'priority'
        ]


class CommentForm(forms.ModelForm):

    class Meta:
        model = TicketComment

        fields = ['comment']