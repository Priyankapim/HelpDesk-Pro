from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count

from tickets.models import Ticket


@login_required
def reports_dashboard(request):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        return redirect("dashboard")

    department_report = (
        Ticket.objects.values("department__name")
        .annotate(total=Count("id"))
        .order_by("department__name")
    )

    priority_report = (
        Ticket.objects.values("priority")
        .annotate(total=Count("id"))
        .order_by("priority")
    )

    agent_report = (
        Ticket.objects.values(
            "assigned_to__first_name",
            "assigned_to__last_name",
            "assigned_to__email",
        )
        .annotate(total=Count("id"))
    )

    context = {
        "department_report": department_report,
        "priority_report": priority_report,
        "agent_report": agent_report,
    }

    return render(
        request,
        "reports_dashboard.html",
        context,
    )
