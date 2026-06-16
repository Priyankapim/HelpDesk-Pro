from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Department


@login_required
def department_list(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    departments = Department.objects.all().order_by('name')

    return render(
        request,
        'department_list.html',
        {
            'departments': departments
        }
    )


@login_required
def add_department(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    if request.method == "POST":

        Department.objects.create(

            name=request.POST.get("name"),

            description=request.POST.get("description")

        )

        return redirect("department_list")

    return render(
        request,
        "add_department.html"
    )


@login_required
def edit_department(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(
        Department,
        id=department_id
    )

    if request.method == "POST":

        department.name = request.POST.get("name")

        department.description = request.POST.get(
            "description"
        )

        department.save()

        return redirect("department_list")

    return render(

        request,

        "edit_department.html",

        {

            "department": department

        }

    )


@login_required
def delete_department(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(
        Department,
        id=department_id
    )

    department.delete()

    return redirect("department_list")
