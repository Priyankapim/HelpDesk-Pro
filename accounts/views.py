from datetime import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from tickets.models import Ticket
from .models import User
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from tickets.models import Department
import csv
from django.http import HttpResponse
from .forms import ChangePasswordForm
import re
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

def login_view(request):

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

    return render(request, "login.html")


@login_required
def dashboard_view(request):
    days_filter = request.GET.get("days", "30")

    if days_filter == "7":
        filter_days = 7
    elif days_filter == "90":
        filter_days = 90
    else:
        filter_days = 30

    if request.user.role == "EMPLOYEE":
        tickets = Ticket.objects.filter(
            created_by=request.user
        )

    elif request.user.role == "AGENT":
        tickets = Ticket.objects.filter(
            assigned_to=request.user
        )

    else:
        tickets = Ticket.objects.all()

    total_tickets = tickets.count()

    breached_tickets = sum(
        1 for ticket in tickets
        if timezone.now() > ticket.sla_deadline
        and ticket.status not in ["Resolved", "Closed"]
    )

    if total_tickets > 0:
        sla_rate = round(
            ((total_tickets - breached_tickets) / total_tickets) * 100
        )
    else:
        sla_rate = None

    days = []
    ticket_counts = []

    for i in range(filter_days - 1, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        days.append(date.strftime("%d %b"))

        ticket_counts.append(
            tickets.filter(
                created_at__date=date
            ).count()
        )

    status_labels = [
        'Open',
        'In Progress',
        'Resolved',
        'Closed'
    ]

    status_data = [
        tickets.filter(status='Open').count(),
        tickets.filter(status='In Progress').count(),
        tickets.filter(status='Resolved').count(),
        tickets.filter(status='Closed').count(),
    ]

    priority_labels = [
        'Low',
        'Medium',
        'High',
        'Critical'
    ]

    status_flow = [
        "Open",
        "Assigned",
        "In Progress",
        "Resolved",
        "Closed"
    ]

    priority_data = [
        tickets.filter(priority='Low').count(),
        tickets.filter(priority='Medium').count(),
        tickets.filter(priority='High').count(),
        tickets.filter(priority='Critical').count(),
    ]

    department_stats = tickets.values(
        'department__name'
    ).annotate(
        total=Count('id')
    )

    department_labels = []
    department_data = []

    for item in department_stats:
        department_labels.append(
            item['department__name']
        )

        department_data.append(
            item['total']
        )


    context = {
        "total_tickets": total_tickets,
        "open_tickets": tickets.filter(
            status="Open"
        ).count(),

        "in_progress_tickets": tickets.filter(
            status="In Progress"
        ).count(),

        "resolved_tickets": tickets.filter(
            status="Resolved"
        ).count(),

        "closed_tickets": tickets.filter(
            status="Closed"
        ).count(),

        "critical_tickets": tickets.filter(
            priority="Critical"
        ).count(),

        "pending_tickets": tickets.filter(
            status="Open"
        ).count(),

        "escalated_tickets": tickets.filter(
            priority="Critical",
            status="In Progress"
        ).count(),

        "sla_rate": sla_rate,

        "recent_tickets": tickets.order_by(
            "-created_at"
        )[:6],

        "departments": Department.objects.all(),

        "status_labels": status_labels,
        "status_data": status_data,

        "priority_labels": priority_labels,
        "priority_data": priority_data,

        "department_labels": department_labels,
        "department_data": department_data,

        "trend_labels": days,
        "trend_data": ticket_counts,

        "selected_days": days_filter,
        "sla_rate": sla_rate,
        "breached_tickets": breached_tickets,

        'status_flow': status_flow,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def users_list(request):

    if request.user.role not in [
        'ADMIN',
        'SUPER_ADMIN'
    ]:
        return redirect('dashboard')

    users = User.objects.all().order_by('first_name')

    return render(
        request,
        'users_list.html',
        {
            'users': users
        }
    )


@login_required
def edit_user(request, user_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        role = request.POST.get("role")
        user.role = role
        user.save()
        return redirect("users_list")

    return render(
        request,
        "edit_user.html",
        {
            "user_obj": user
        }
    )


@login_required
def export_tickets_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="tickets.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Ticket No',
        'Title',
        'Status',
        'Priority',
        'Department',
        'Created Date'
    ])

    tickets = Ticket.objects.all()

    for ticket in tickets:

        writer.writerow([
            ticket.ticket_number,
            ticket.title,
            ticket.status,
            ticket.priority,
            ticket.department.name if ticket.department else '',
            ticket.created_at.strftime('%d-%m-%Y')
        ])

    return response



@login_required
def change_password(request):

    form = ChangePasswordForm()

    if request.method == "POST":

        form = ChangePasswordForm(request.POST)

        if form.is_valid():

            current_password = form.cleaned_data["current_password"]
            new_password = form.cleaned_data["new_password"]
            confirm_password = form.cleaned_data["confirm_password"]

            if not request.user.check_password(current_password):

                messages.error(
                    request,
                    "Current password is incorrect."
                )

            elif new_password != confirm_password:

                messages.error(
                    request,
                    "New Password and Confirm Password do not match."
                )

            elif len(new_password) < 8:

                messages.error(
                    request,
                    "Password must be at least 8 characters long."
                )

            elif not re.search(r"[A-Z]", new_password):

                messages.error(
                    request,
                    "Password must contain at least one uppercase letter."
                )

            elif not re.search(r"[a-z]", new_password):

                messages.error(
                    request,
                    "Password must contain at least one lowercase letter."
                )

            elif not re.search(r"\d", new_password):

                messages.error(
                    request,
                    "Password must contain at least one number."
                )

            elif not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):

                messages.error(
                    request,
                    "Password must contain at least one special character."
                )

            else:

                request.user.set_password(new_password)
                request.user.save()

                update_session_auth_hash(
                    request,
                    request.user
                )

                messages.success(
                    request,
                    "Password changed successfully."
                )

                return redirect("dashboard")

    return render(
        request,
        "change_password.html",
        {
            "form": form
        }
    )