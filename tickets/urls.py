from django.urls import path
from .views import create_ticket,my_tickets, ticket_detail, all_tickets, assigned_tickets, delete_notification
from .views import open_notification, global_search, ai_triage, reports, export_tickets_excel, export_tickets_pdf
from .views import export_reports_excel, export_reports_pdf,  ai_assistant_view, ai_assistant_chat
from .views import category_list, add_category, edit_category, toggle_category, delete_category

urlpatterns = [
    path('create/', create_ticket, name='create_ticket'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('detail/<int:ticket_id>/', ticket_detail, name='ticket_detail' ),
    path('all/', all_tickets, name='all_tickets' ),
    path('assigned/', assigned_tickets, name='assigned_tickets' ),
    path("notification/delete/<int:notification_id>/", delete_notification, name="delete_notification" ),
    path("notification/<int:notification_id>/", open_notification, name="open_notification"),
    path("search/", global_search, name="global_search" ),
    path("ai-triage/", ai_triage, name="ai_triage" ),
    path("reports/", reports, name="reports" ),
    path("reports/excel/", export_tickets_excel, name="export_tickets_excel"),
    path("reports/pdf/", export_tickets_pdf, name="export_tickets_pdf"),
    path("reports/export/excel/", export_reports_excel, name="export_reports_excel"),
    path("reports/export/pdf/", export_reports_pdf, name="export_reports_pdf" ),
    path("ai-assistant/", ai_assistant_view, name="ai_assistant" ),
    path("ai-assistant/chat/", ai_assistant_chat, name="ai_assistant_chat" ),
    path("categories/", category_list, name="category_list"),
    path("categories/add/", add_category, name="add_category"),
    path("categories/edit/<int:category_id>/", edit_category, name="edit_category"),
    path("categories/toggle/<int:category_id>/", toggle_category, name="toggle_category"),
    path("categories/delete/<int:category_id>/", delete_category, name="delete_category"),
]

