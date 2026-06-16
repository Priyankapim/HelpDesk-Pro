from django.urls import path

from .views import *

urlpatterns = [

    path("", department_list, name="department_list"),

    path("add/", add_department, name="add_department" ),

    path("edit/<int:department_id>/", edit_department, name="edit_department" ),

    path("delete/<int:department_id>/", delete_department, name="delete_department" ),

]