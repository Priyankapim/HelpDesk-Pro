from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from auditlogs.utils import log_activity
from .models import Department, Category


@login_required
def department_list(request):

    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    departments = Department.objects.all().order_by('name').prefetch_related('categories')

    if request.user.role != 'SUPER_ADMIN':
        departments = departments.filter(tenant=request.user.tenant)

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

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Department name is required.")
            return redirect("department_list")

        department = Department.objects.create(
            name=name,
            description=request.POST.get("description", ""),
            sla_critical=request.POST.get("sla_critical") or 2,
            sla_high=request.POST.get("sla_high") or 8,
            sla_medium=request.POST.get("sla_medium") or 24,
            sla_low=request.POST.get("sla_low") or 72,
        )

        log_activity(
            actor=request.user,
            action="department.created",
            action_label="Department created",
            module="DEPARTMENTS",
            target=department.name,
            severity="INFO",
        )

        messages.success(request, f"Department '{name}' created.")

        return redirect("department_list")

    return redirect("department_list")


@login_required
def edit_department(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(
        Department,
        id=department_id
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Department name is required.")
            return redirect("department_list")

        department.name = name
        department.description = request.POST.get("description", "")
        department.sla_critical = request.POST.get("sla_critical") or 2
        department.sla_high = request.POST.get("sla_high") or 8
        department.sla_medium = request.POST.get("sla_medium") or 24
        department.sla_low = request.POST.get("sla_low") or 72

        department.save()

        log_activity(
            actor=request.user,
            action="department.updated",
            action_label="Department updated",
            module="DEPARTMENTS",
            target=department.name,
            severity="INFO",
        )

        messages.success(request, f"Department '{name}' updated.")

        return redirect("department_list")

    return redirect("department_list")


@login_required
def toggle_department(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(
        Department,
        id=department_id
    )

    department.is_active = not department.is_active
    department.save()

    log_activity(
        actor=request.user,
        action="department.status_toggled",
        action_label="Department status changed",
        module="DEPARTMENTS",
        target=department.name,
        severity="WARNING",
    )

    if department.is_active:
        messages.success(request, f"'{department.name}' marked as active.")
    else:
        messages.success(request, f"'{department.name}' marked as inactive.")

    return redirect("department_list")


@login_required
def delete_department(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(
        Department,
        id=department_id
    )

    department_name = department.name

    department.delete()

    log_activity(
        actor=request.user,
        action="department.deleted",
        action_label="Department deleted",
        module="DEPARTMENTS",
        target=department_name,
        severity="CRITICAL",
    )

    return redirect("department_list")


@login_required
def add_category(request, department_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    department = get_object_or_404(Department, id=department_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("department_list")

        if Category.objects.filter(department=department, name__iexact=name).exists():
            messages.error(request, f"'{name}' already exists under {department.name}.")
            return redirect("department_list")

        Category.objects.create(
            department=department,
            name=name,
        )

        log_activity(
            actor=request.user,
            action="category.created",
            action_label="Category created",
            module="DEPARTMENTS",
            target=f"{department.name} - {name}",
            severity="INFO",
        )

        messages.success(request, f"Category '{name}' added under {department.name}.")

    return redirect("department_list")


@login_required
def edit_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("department_list")

        if Category.objects.filter(
            department=category.department,
            name__iexact=name
        ).exclude(id=category.id).exists():
            messages.error(request, f"'{name}' already exists under {category.department.name}.")
            return redirect("department_list")

        old_name = category.name
        category.name = name
        category.save()

        log_activity(
            actor=request.user,
            action="category.updated",
            action_label="Category renamed",
            module="DEPARTMENTS",
            target=f"{category.department.name} - {old_name} -> {name}",
            severity="INFO",
        )

        messages.success(request, f"Category renamed to '{name}'.")

    return redirect("department_list")


@login_required
def toggle_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id)

    category.is_active = not category.is_active
    category.save()

    log_activity(
        actor=request.user,
        action="category.status_toggled",
        action_label="Category status changed",
        module="DEPARTMENTS",
        target=f"{category.department.name} - {category.name}",
        severity="WARNING",
    )

    if category.is_active:
        messages.success(request, f"'{category.name}' marked as active.")
    else:
        messages.success(request, f"'{category.name}' marked as inactive.")

    return redirect("department_list")


@login_required
def delete_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(Category, id=category_id)

    category_label = f"{category.department.name} - {category.name}"
    category.delete()

    log_activity(
        actor=request.user,
        action="category.deleted",
        action_label="Category deleted",
        module="DEPARTMENTS",
        target=category_label,
        severity="CRITICAL",
    )

    messages.success(request, "Category deleted.")

    return redirect("department_list")