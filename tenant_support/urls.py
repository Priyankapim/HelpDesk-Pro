from django.urls import path

from .views import (
    support_inbox,
    support_detail,
    my_support_requests,
    my_support_detail,
)

urlpatterns = [

    # SuperAdmin side
    path('', support_inbox, name='support_inbox'),
    path('<int:request_id>/', support_detail, name='support_detail'),

    # Tenant Admin side
    path('mine/', my_support_requests, name='my_support_requests'),
    path('mine/<int:request_id>/', my_support_detail, name='my_support_detail'),

]
