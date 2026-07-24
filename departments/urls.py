from django.urls import path

from .views import *

urlpatterns = [

    path("", department_list, name="department_list"),

    path("add/", add_department, name="add_department" ),

    path("edit/<int:department_id>/", edit_department, name="edit_department" ),

    path("toggle/<int:department_id>/", toggle_department, name="toggle_department" ),

    path("delete/<int:department_id>/", delete_department, name="delete_department" ),

    path("category/add/<int:department_id>/", add_category, name="add_category"),

    path("category/edit/<int:category_id>/", edit_category, name="edit_category"),

    path("category/toggle/<int:category_id>/", toggle_category, name="toggle_category"),

    path("category/delete/<int:category_id>/", delete_category, name="delete_category"),

]