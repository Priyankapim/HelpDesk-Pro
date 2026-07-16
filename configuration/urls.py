from django.urls import path

from .views import (
    config_home,
    save_sla_rules,
    save_working_hours,
    add_holiday,
    delete_holiday,
    add_escalation_rule,
    edit_escalation_rule,
    delete_escalation_rule,
    add_email_template,
    edit_email_template,
    delete_email_template,
)

urlpatterns = [

    path('', config_home, name='config_home'),

    path('sla/<int:department_id>/save/', save_sla_rules, name='save_sla_rules'),

    path('working-hours/save/', save_working_hours, name='save_working_hours'),

    path('holidays/add/', add_holiday, name='add_holiday'),
    path('holidays/<int:holiday_id>/delete/', delete_holiday, name='delete_holiday'),

    path('escalation/add/', add_escalation_rule, name='add_escalation_rule'),
    path('escalation/<int:rule_id>/edit/', edit_escalation_rule, name='edit_escalation_rule'),
    path('escalation/<int:rule_id>/delete/', delete_escalation_rule, name='delete_escalation_rule'),

    path('templates/add/', add_email_template, name='add_email_template'),
    path('templates/<int:template_id>/edit/', edit_email_template, name='edit_email_template'),
    path('templates/<int:template_id>/delete/', delete_email_template, name='delete_email_template'),

]
