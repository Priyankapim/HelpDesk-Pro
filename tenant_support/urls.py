from django.urls import path

from .views import support_inbox, support_detail, raise_support_request

urlpatterns = [

    path('', support_inbox, name='support_inbox'),
    path('<int:request_id>/', support_detail, name='support_detail'),
    path('raise/', raise_support_request, name='raise_support_request'),

]
