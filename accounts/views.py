
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from tickets.models import Ticket
from .models import User
from django.shortcuts import get_object_or_404




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

    if request.user.role == "EMPLOYEE":

        tickets = Ticket.objects.filter(created_by=request.user)

    elif request.user.role == "AGENT":

        tickets = Ticket.objects.filter(assigned_to=request.user)

    else:  # ADMIN / SUPER_ADMIN

        tickets = Ticket.objects.all()

    context = {

        "total_tickets": tickets.count(),

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

        "recent_tickets": tickets.order_by(
            "-created_at"
        )[:5],
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