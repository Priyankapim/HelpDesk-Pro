from django.urls import path
from .views import create_ticket,my_tickets, ticket_detail, all_tickets, assigned_tickets, delete_notification, open_notification

urlpatterns = [
    path('create/', create_ticket, name='create_ticket'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('detail/<int:ticket_id>/', ticket_detail, name='ticket_detail' ),
    path('all/', all_tickets, name='all_tickets' ),
    path('assigned/', assigned_tickets, name='assigned_tickets' ),
    path("notification/delete/<int:notification_id>/", delete_notification, name="delete_notification" ),
    path("notification/<int:notification_id>/", open_notification, name="open_notification"),
]

