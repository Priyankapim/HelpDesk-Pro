from django.urls import path
from .views import login_view, dashboard_view, logout_view, users_list, edit_user, export_tickets_csv, change_password
from .views import invitation_list, invite_user, accept_invitation, revoke_invitation, delete_invitation, resend_invitation
from .views import security_settings_view, update_security_settings, logout_other_sessions, logout_session

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('users/', users_list, name='users_list' ),
    path( "users/edit/<int:user_id>/", edit_user, name="edit_user" ),
    path('export-csv/', export_tickets_csv, name='export_tickets_csv'),
    path("change-password/", change_password, name="change_password" ),
    path("users/invitations/", invitation_list, name="invitation_list" ),
    path("users/invite/", invite_user, name="invite_user" ),
    path("users/accept/<uuid:token>/", accept_invitation, name="accept_invitation" ),
    path("users/invitations/revoke/<int:invitation_id>/", revoke_invitation, name="revoke_invitation" ),
    path("users/invitations/delete/<int:invitation_id>/", delete_invitation, name="delete_invitation" ),
    path("users/invitations/resend/<int:invitation_id>/", resend_invitation, name="resend_invitation" ),
    path("security/", security_settings_view, name="security_settings" ),
    path("security/update/", update_security_settings, name="update_security_settings" ),
    path("security/logout-others/", logout_other_sessions, name="logout_other_sessions" ),
    path("security/logout-session/<str:session_key>/", logout_session, name="logout_session" ),
]