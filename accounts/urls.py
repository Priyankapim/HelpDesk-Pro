

from django.urls import path
from .views import login_view, dashboard_view, logout_view, users_list, edit_user, export_tickets_csv


urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('users/', users_list, name='users_list' ),
    path( "users/edit/<int:user_id>/", edit_user, name="edit_user" ),
    path('export-csv/', export_tickets_csv, name='export_tickets_csv'),
]