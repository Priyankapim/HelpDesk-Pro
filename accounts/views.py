
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from tickets.models import Ticket


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

    total_tickets = Ticket.objects.count()

    open_tickets = Ticket.objects.filter(
        status='Open'
    ).count()

    in_progress_tickets = Ticket.objects.filter(
        status='In Progress'
    ).count()

    resolved_tickets = Ticket.objects.filter(
        status='Resolved'
    ).count()

    closed_tickets = Ticket.objects.filter(
        status='Closed'
    ).count()

    context = {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
        'closed_tickets': closed_tickets,
    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )

