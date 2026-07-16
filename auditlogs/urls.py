from django.urls import path

from .views import audit_log_list, audit_log_export_csv

urlpatterns = [

    path('', audit_log_list, name='audit_logs'),

    path('export-csv/', audit_log_export_csv, name='audit_logs_export_csv'),

]
