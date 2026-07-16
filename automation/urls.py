from django.urls import path

from .views import *

urlpatterns = [

    path("", automation_list, name="automation_list"),

    path("add/", add_automation_rule, name="add_automation_rule"),

    path("edit/<int:rule_id>/", edit_automation_rule, name="edit_automation_rule"),

    path("toggle/<int:rule_id>/", toggle_automation_rule, name="toggle_automation_rule"),

    path("delete/<int:rule_id>/", delete_automation_rule, name="delete_automation_rule"),

]