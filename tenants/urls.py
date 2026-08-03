from django.urls import path

from .views import (
    tenant_list,
    create_tenant,
    tenant_detail,
    suspend_tenant,
    reactivate_tenant,
    delete_tenant,
    send_invite,
    revoke_invite,
    resend_invite,
    accept_invite,
)

urlpatterns = [

    path('', tenant_list, name='tenant_list'),
    path('create/', create_tenant, name='create_tenant'),
    path('<int:tenant_id>/', tenant_detail, name='tenant_detail'),

    path('<int:tenant_id>/suspend/', suspend_tenant, name='suspend_tenant'),
    path('<int:tenant_id>/reactivate/', reactivate_tenant, name='reactivate_tenant'),
    path('<int:tenant_id>/delete/', delete_tenant, name='delete_tenant'),

    path('<int:tenant_id>/invites/send/', send_invite, name='send_invite'),
    path('invites/<int:invite_id>/revoke/', revoke_invite, name='revoke_invite'),
    path('invites/<int:invite_id>/resend/', resend_invite, name='resend_invite'),

    path('invites/accept/<uuid:token>/', accept_invite, name='accept_invite'),

]