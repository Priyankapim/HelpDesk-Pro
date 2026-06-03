from django.urls import path
from .views import create_ticket,my_tickets, ticket_detail

urlpatterns = [
    path('create/', create_ticket, name='create_ticket'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('detail/<int:ticket_id>/', ticket_detail, name='ticket_detail' ),
]

