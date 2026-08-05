from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from notifications.utils import send_ticket_email
from .forms import TicketForm
from .models import Ticket, TicketComment, Notification, Category
from accounts.models import User
from django.contrib import messages
from auditlogs.utils import log_activity
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from departments.models import Department
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
import json
from .ai_triage import ai_triage
from django.db.models import Count
from django.db.models.functions import TruncMonth
from openpyxl import Workbook
from django.http import HttpResponse
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from .services.ai_service import ai_assistant_reply
from departments.utils import get_department_category_map
import json


from django.http import HttpResponse
from accounts.models import User


def debug_tenants_view(request):

    if not request.user.is_authenticated or request.user.role != "SUPER_ADMIN":
        return HttpResponse("Not allowed", status=403)

    lines = ["---- USERS ----"]

    for user in User.objects.all().order_by("id"):
        lines.append(
            f"id={user.id} email={user.email} role={user.role} "
            f"tenant_id={user.tenant_id} "
            f"tenant_name={user.tenant.name if user.tenant_id else None}"
        )

    lines.append("---- TICKETS ----")

    for ticket in Ticket.objects.all().order_by("id"):
        lines.append(
            f"id={ticket.id} number={ticket.ticket_number} "
            f"created_by={ticket.created_by.email if ticket.created_by_id else None} "
            f"created_by_tenant={ticket.created_by.tenant_id if ticket.created_by_id else None} "
            f"ticket_tenant_id={ticket.tenant_id}"
        )

    return HttpResponse("<pre>" + "\n".join(lines) + "</pre>")


def _scope_tickets_qs(request):
    """
    Returns the base Ticket queryset scoped to the requesting user's
    tenant when they're an ADMIN. SUPER_ADMIN does not see tenant-
    internal tickets — they use the Support Requests inbox instead.
    """
    if request.user.role == "ADMIN":
        return Ticket.objects.filter(tenant_id=request.user.tenant_id)
    if request.user.role == "SUPER_ADMIN":
        return Ticket.objects.none()
    return Ticket.objects.all()


def create_ticket(request):
    if request.user.role == "SUPER_ADMIN":
        return redirect("dashboard")

    if request.method == "POST":
        form = TicketForm(request.POST, user=request.user)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()

            Notification.objects.create(
                user=request.user,
                ticket=ticket,
                title="Ticket Created",
                message=f'Your ticket "{ticket.title}" has been created.'
            )

            send_ticket_email(

                subject="Ticket Created Successfully",

                message=f"""
            Hello {request.user.first_name or request.user.email},

            Your support ticket has been created successfully.

            Ticket Number: {ticket.ticket_number}

            Title: {ticket.title}

            Priority: {ticket.priority}

            Department: {ticket.department}

            Status: {ticket.status}

            Our support team will contact you shortly.


            Thank you.

            """,

                recipient=request.user.email

            )

            from automation.engine import run_automation_rules
            run_automation_rules("TICKET_CREATED", ticket)

            return redirect('dashboard')

    else:

        form = TicketForm(user=request.user)

    return render(
        request,
        'tickets/create_ticket.html',
        {
            'form': form,
            'department_category_map': json.dumps(get_department_category_map()),
        }
    )


@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    # Search
    search = request.GET.get("search")
    if search:
        tickets = tickets.filter(

            Q(ticket_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search)

        )

    # Status Filter
    status = request.GET.get("status")
    if status:
        tickets = tickets.filter(status=status)

    # Priority Filter
    priority = request.GET.get("priority")
    if priority:
        tickets = tickets.filter(priority=priority)

    # Pagination
    paginator = Paginator(tickets, 10)
    page = request.GET.get("page")
    tickets = paginator.get_page(page)

    total_tickets = Ticket.objects.filter(
        created_by=request.user
    ).count()

    user_tickets = Ticket.objects.filter(
        created_by=request.user
    )

    sla_breached = sum(
        1 for ticket in user_tickets
        if timezone.now() > ticket.sla_deadline
        and ticket.status not in ["Resolved", "Closed"]
    )

    context = {
        "tickets": tickets,
        "search": search,
        "selected_status": status,
        "selected_priority": priority,
        "status_choices": Ticket.STATUS_CHOICES,
        "priority_choices": Ticket.PRIORITY_CHOICES,
        "total_tickets": total_tickets,
        "sla_breached": sla_breached,
    }

    return render(
        request, "tickets/my_tickets.html", context,
    )


def all_tickets(request):
    if request.user.role not in ["ADMIN"]:
        return redirect("dashboard")

    tickets = Ticket.objects.select_related(
        "department",
        "created_by",
        "assigned_to"
    ).order_by("-created_at")

    if request.user.role == "ADMIN":
        tickets = tickets.filter(tenant_id=request.user.tenant_id)
    elif request.user.role == "SUPER_ADMIN":
        tickets = tickets.none()

    # -- Search --

    search = request.GET.get("search")
    if search:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(created_by__email__icontains=search)

        )

    # -- Status --

    status = request.GET.get("status")
    if status:
        tickets = tickets.filter(status=status)

    # -- Priority --

    priority = request.GET.get("priority")
    if priority:
        tickets = tickets.filter(priority=priority)

    # -- Department --

    department = request.GET.get("department")
    if department:
        tickets = tickets.filter(department_id=department)

    # -- Assigned --

    assigned = request.GET.get("assigned")
    if assigned == "yes":
        tickets = tickets.filter(
            assigned_to__isnull=False
        )

    elif assigned == "no":
        tickets = tickets.filter(
            assigned_to__isnull=True
        )

    paginator = Paginator(tickets, 10)
    page = request.GET.get("page")
    tickets = paginator.get_page(page)

    if request.user.role == "ADMIN":
        dept_qs = Department.objects.filter(tenant_id=request.user.tenant_id)
        base_qs = Ticket.objects.filter(tenant_id=request.user.tenant_id)
    elif request.user.role == "SUPER_ADMIN":
        dept_qs = Department.objects.none()
        base_qs = Ticket.objects.none()
    else:
        dept_qs = Department.objects.all()
        base_qs = Ticket.objects.all()

    context = {
        "tickets": tickets,
        "search": search,
        "selected_status": status,
        "selected_priority": priority,
        "selected_department": department,
        "selected_assigned": assigned,
        "status_choices": Ticket.STATUS_CHOICES,
        "priority_choices": Ticket.PRIORITY_CHOICES,
        "departments": dept_qs,
        "total_tickets": base_qs.count(),
        "open_tickets": base_qs.filter(status="Open").count(),
        "resolved_tickets": base_qs.filter(status="Resolved").count(),
        "unassigned": base_qs.filter(assigned_to__isnull=True).count(),
    }

    return render(
        request, "tickets/all_tickets.html", context,
    )


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        Ticket,
        id=ticket_id
    )

    # Employee can only view own tickets
    if request.user.role == 'EMPLOYEE':

        if ticket.created_by != request.user:
            return redirect('dashboard')

    # Agent can only view assigned tickets
    if request.user.role == 'AGENT':

        if ticket.assigned_to != request.user:
            return redirect('dashboard')

    agents = User.objects.filter(
        role='AGENT'
    )

    comments = ticket.comments.all().order_by('-created_at')

    if request.method == 'POST':
        agent_id = request.POST.get('assigned_to')

        if (
                agent_id and
                request.user.role in ['ADMIN', 'SUPER_ADMIN']
        ):

            assigned_agent = User.objects.get(id=agent_id)
            old_agent = ticket.assigned_to

            ticket.assigned_to = assigned_agent
            ticket.save()

            if old_agent != assigned_agent:
                send_ticket_email(

                    subject="New Ticket Assigned",

                    message=f"""
        Hello {assigned_agent.first_name or assigned_agent.email},

        A new ticket has been assigned to you.

        Ticket Number: {ticket.ticket_number}

        Title: {ticket.title}

        Priority: {ticket.priority}

        Please login to the HelpDesk portal and start working on it.

        Thank you.
        """,
                    recipient=assigned_agent.email
                )

                from automation.engine import run_automation_rules
                run_automation_rules("TICKET_ASSIGNED", ticket)

        old_status = ticket.status

        new_status = request.POST.get("status")

        if (
                new_status and
                request.user.role in ['ADMIN', 'SUPER_ADMIN', 'AGENT']
        ):

            if old_status != new_status:
                ticket.status = new_status
                ticket.save()

                send_ticket_email(

                    subject="Ticket Status Updated",

                    message=f"""
        Hello {ticket.created_by.first_name or ticket.created_by.email},

        Your ticket status has been updated.

        Ticket Number: {ticket.ticket_number}

        Title: {ticket.title}

        Previous Status: {old_status}

        Current Status: {new_status}

        Thank you.
        """,
                    recipient=ticket.created_by.email
                )

                from automation.engine import run_automation_rules
                run_automation_rules("STATUS_CHANGED", ticket,
                                     extra={"old_status": old_status, "new_status": new_status})

        comment_text = request.POST.get('comment')

        if comment_text:
            TicketComment.objects.create(
                ticket=ticket,
                user=request.user,
                comment=comment_text
            )

            from automation.engine import run_automation_rules
            run_automation_rules("COMMENT_ADDED", ticket)

        ticket.save()

    return render(
        request,
        'tickets/ticket_detail.html',
        {
            'ticket': ticket,
            'agents': agents,
            'comments': comments
        }
    )


@login_required
def assigned_tickets(request):
    if request.user.role != 'AGENT':
        return redirect('dashboard')

    tickets = Ticket.objects.filter(
        assigned_to=request.user
    ).order_by('-created_at')

    return render(

        request, 'tickets/assigned_tickets.html',
        {'tickets': tickets}
    )


@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.delete()

    return redirect(request.META.get("HTTP_REFERER", "dashboard"))


def open_notification(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.is_read = True
    notification.save()

    return redirect(
        "ticket_detail",
        notification.ticket.id
    )


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()

    results = []

    role = request.user.role

    if query:

        # == Tickets ==

        ticket_filter = (
                Q(ticket_number__icontains=query) |
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(status__icontains=query) |
                Q(priority__icontains=query) |
                Q(department__name__icontains=query)
        )

        if role == "EMPLOYEE":

            tickets = Ticket.objects.filter(
                created_by=request.user
            ).filter(ticket_filter).distinct()[:5]

        elif role == "AGENT":

            tickets = Ticket.objects.filter(
                assigned_to=request.user
            ).filter(ticket_filter).distinct()[:5]

        elif role == "ADMIN":

            tickets = Ticket.objects.filter(
                tenant_id=request.user.tenant_id
            ).filter(ticket_filter).distinct()[:5]


        else:  # SUPER_ADMIN

            tickets = Ticket.objects.none()

        for ticket in tickets:
            results.append({
                "type": "ticket",
                "title": ticket.ticket_number,
                "subtitle": ticket.title,
                "extra": f"{ticket.department.name} • {ticket.status}",
                "url": reverse("ticket_detail", args=[ticket.id])
            })

        # == Users (Only Admin & Super Admin) ==

        if role in ["ADMIN", "SUPER_ADMIN"]:

            users = User.objects.filter(

                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)

            )

            if role == "ADMIN":
                users = users.filter(tenant_id=request.user.tenant_id)

            users = users[:5]

            for user in users:
                results.append({
                    "type": "user",
                    "title": f"{user.first_name} {user.last_name}",
                    "subtitle": user.email,
                    "extra": user.role,
                    "url": reverse("users_list")
                })

    
        # == Departments ==

        departments = Department.objects.filter(
            name__icontains=query
        )

        if role == "ADMIN":
            departments = departments.filter(tenant_id=request.user.tenant_id)

        departments = departments[:5]

        for dept in departments:
            results.append({
                "type": "department",
                "title": dept.name,
                "subtitle": "Department",
                "extra": dept.description if dept.description else "",
                "url": reverse("department_list")
            })

    return JsonResponse(results, safe=False)


@require_POST
def ai_triage_view(request):
    try:

        data = json.loads(request.body)
        subject = data.get("subject", "")
        description = data.get("description", "")
        result = ai_triage(subject, description)

        return JsonResponse({
            "success": True,
            "result": result
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })


@login_required
def reports(request):
    if request.user.role == "SUPER_ADMIN":
        return redirect("dashboard")

    if request.user.role == "ADMIN":
        base_qs = Ticket.objects.filter(tenant_id=request.user.tenant_id)
        departments = Department.objects.filter(tenant_id=request.user.tenant_id)
    elif request.user.role == "SUPER_ADMIN":
        base_qs = Ticket.objects.none()
        departments = Department.objects.none()
    else:
        base_qs = Ticket.objects.all()
        departments = Department.objects.all()

    total_tickets = base_qs.count()

    department_report = (
        base_qs
        .values("department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    priority_report = (
        base_qs
        .values("priority")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    agent_report = (
        base_qs
        .filter(assigned_to__isnull=False)
        .values(
            "assigned_to__first_name",
            "assigned_to__last_name",
            "assigned_to__email"
        )
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    status_report = (
        base_qs
        .values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    category_report = (
        base_qs
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    monthly_report = (
        base_qs
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("-month")
    )

    # SLA Report
    breached = 0
    within = 0

    for ticket in base_qs:

        if ticket.status in ["Resolved", "Closed"]:
            within += 1

        elif timezone.now() > ticket.sla_deadline:
            breached += 1

        else:
            within += 1

    sla_report = [

        {
            "sla": "Within SLA",
            "total": within
        },

        {
            "sla": "Breached",
            "total": breached
        }

    ]

    context = {

        "total_tickets": total_tickets,
        "departments": departments,
        "status_choices": Ticket.STATUS_CHOICES,
        "priority_choices": Ticket.PRIORITY_CHOICES,
        "department_report": department_report,
        "priority_report": priority_report,
        "agent_report": agent_report,
        "status_report": status_report,
        "category_report": category_report,
        "monthly_report": monthly_report,
        "sla_report": sla_report,

    }

    return render(
        request,
        "reports_dashboard.html",
        context
    )


@login_required
def export_tickets_excel(request):

    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets Report"

    ws.append([
        "Ticket No",
        "Title",
        "Department",
        "Status",
        "Priority",
        "Assigned To",
        "Created Date"
    ])

    tickets = _scope_tickets_qs(request).select_related(
        "department",
        "assigned_to"
    )

    for ticket in tickets:
        ws.append([

            ticket.ticket_number,

            ticket.title,

            ticket.department.name if ticket.department else "",

            ticket.status,

            ticket.priority,

            str(ticket.assigned_to) if ticket.assigned_to else "Unassigned",

            ticket.created_at.strftime("%d-%m-%Y"),

        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Tickets_Report.xlsx"'
    )

    wb.save(response)

    return response


@login_required
def export_tickets_pdf(request):
    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        'attachment; filename="Tickets_Report.pdf"'
    )

    doc = SimpleDocTemplate(response)

    data = [[
        "Ticket",
        "Department",
        "Status",
        "Priority",
        "Created"
    ]]

    tickets = _scope_tickets_qs(request).select_related("department")

    for ticket in tickets:
        data.append([

            ticket.ticket_number,

            ticket.department.name if ticket.department else "",

            ticket.status,

            ticket.priority,

            ticket.created_at.strftime("%d-%m-%Y")

        ])

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),

        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 1, colors.grey),

        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

    ]))

    doc.build([table])

    return response


@login_required
def export_reports_excel(request):

    wb = Workbook()
    ws = wb.active
    ws.title = "Reports"

    base_qs = _scope_tickets_qs(request)

    # ================= Department =================

    ws.append(["Department Report"])
    ws.append(["Department", "Total Tickets"])

    department_report = (
        base_qs
        .values("department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in department_report:
        ws.append([
            row["department__name"],
            row["total"]
        ])

    ws.append([])

    # ================= Priority =================

    ws.append(["Priority Report"])
    ws.append(["Priority", "Total Tickets"])

    priority_report = (
        base_qs
        .values("priority")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in priority_report:
        ws.append([
            row["priority"],
            row["total"]
        ])

    ws.append([])

    # ================= Status =================

    ws.append(["Status Report"])
    ws.append(["Status", "Total Tickets"])

    status_report = (
        base_qs
        .values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in status_report:
        ws.append([
            row["status"],
            row["total"]
        ])

    ws.append([])

    # ================= Agent =================

    ws.append(["Agent Report"])
    ws.append(["Agent", "Assigned Tickets"])

    agent_report = (
        base_qs
        .filter(assigned_to__isnull=False)
        .values(
            "assigned_to__first_name",
            "assigned_to__last_name",
            "assigned_to__email"
        )
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in agent_report:

        name = (
            f"{row['assigned_to__first_name']} {row['assigned_to__last_name']}".strip()
        )

        if not name:
            name = row["assigned_to__email"]

        ws.append([name, row["total"]])

    ws.append([])

    # ================= SLA =================

    within = 0
    breached = 0

    for ticket in base_qs.all():

        if ticket.status in ["Resolved", "Closed"]:
            within += 1

        elif timezone.now() > ticket.sla_deadline:
            breached += 1

        else:
            within += 1

    ws.append(["SLA Report"])
    ws.append(["SLA", "Tickets"])
    ws.append(["Within SLA", within])
    ws.append(["Breached", breached])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Reports.xlsx"'
    )

    wb.save(response)

    return response


@login_required
def export_reports_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        'attachment; filename="Reports.pdf"'
    )

    doc = SimpleDocTemplate(response)

    base_qs = _scope_tickets_qs(request)

    elements = []

    styles = getSampleStyleSheet()

    title = Paragraph(
        "<b>HelpDesk Pro - Reports Summary</b>",
        styles["Heading1"]
    )

    elements.append(title)
    elements.append(Spacer(1, 20))

    # ================= Department =================

    elements.append(
        Paragraph("<b>Department Report</b>", styles["Heading2"])
    )

    department_data = [["Department", "Total Tickets"]]

    department_report = (
        base_qs
        .values("department__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in department_report:
        department_data.append([
            row["department__name"],
            row["total"]
        ])

    table = Table(department_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # ================= Priority =================

    elements.append(
        Paragraph("<b>Priority Report</b>", styles["Heading2"])
    )

    priority_data = [["Priority", "Total Tickets"]]

    priority_report = (
        base_qs
        .values("priority")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in priority_report:
        priority_data.append([
            row["priority"],
            row["total"]
        ])

    table = Table(priority_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # ================= Status =================

    elements.append(
        Paragraph("<b>Status Report</b>", styles["Heading2"])
    )

    status_data = [["Status", "Total Tickets"]]

    status_report = (
        base_qs
        .values("status")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in status_report:
        status_data.append([
            row["status"],
            row["total"]
        ])

    table = Table(status_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # ================= Agent =================

    elements.append(
        Paragraph("<b>Agent Report</b>", styles["Heading2"])
    )

    agent_data = [["Agent", "Assigned Tickets"]]

    agent_report = (
        base_qs
        .filter(assigned_to__isnull=False)
        .values(
            "assigned_to__first_name",
            "assigned_to__last_name",
            "assigned_to__email"
        )
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    for row in agent_report:

        name = (
            f"{row['assigned_to__first_name']} {row['assigned_to__last_name']}".strip()
        )

        if not name:
            name = row["assigned_to__email"]

        agent_data.append([
            name,
            row["total"]
        ])

    table = Table(agent_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 18))

    # ================= SLA =================

    within = 0
    breached = 0

    for ticket in base_qs.all():

        if ticket.status in ["Resolved", "Closed"]:
            within += 1

        elif timezone.now() > ticket.sla_deadline:
            breached += 1

        else:
            within += 1

    elements.append(
        Paragraph("<b>SLA Report</b>", styles["Heading2"])
    )

    sla_data = [
        ["SLA", "Tickets"],
        ["Within SLA", within],
        ["Breached", breached],
    ]

    table = Table(sla_data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(table)

    doc.build(elements)

    return response

@login_required
def ai_assistant_view(request):

    return render(
        request,
        "ai_assistant.html",
        {}
    )


@login_required
@require_POST
def ai_assistant_chat(request):

    try:

        data = json.loads(request.body)

        history = data.get("history", [])

        clean_history = []

        for msg in history[-20:]:

            role = msg.get("role")
            content = (msg.get("content") or "").strip()

            if role in ["user", "assistant"] and content:
                clean_history.append({
                    "role": role,
                    "content": content
                })

        if not clean_history:

            return JsonResponse({
                "success": False,
                "error": "No message provided."
            })

        reply = ai_assistant_reply(clean_history, request.user.role)

        return JsonResponse({
            "success": True,
            "reply": reply
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })



@login_required
def category_list(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    categories = Category.objects.all().order_by('name')

    return render(
        request,
        'category_list.html',
        {
            'categories': categories,
            'active_count': categories.filter(is_active=True).count(),
            'inactive_count': categories.filter(is_active=False).count(),
        }
    )


@login_required
def add_category(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("category_list")

        if Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Category '{name}' already exists.")
            return redirect("category_list")

        category = Category.objects.create(
            name=name,
            description=request.POST.get("description", ""),
        )

        log_activity(
            actor=request.user,
            action="category.created",
            action_label="Category created",
            module="TICKETS",
            target=category.name,
            severity="INFO",
        )

        messages.success(request, f"Category '{name}' created.")

        return redirect("category_list")

    return redirect("category_list")


@login_required
def edit_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(
        Category,
        id=category_id
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Category name is required.")
            return redirect("category_list")

        if Category.objects.filter(name__iexact=name).exclude(id=category.id).exists():
            messages.error(request, f"Category '{name}' already exists.")
            return redirect("category_list")

        category.name = name
        category.description = request.POST.get("description", "")
        category.save()

        log_activity(
            actor=request.user,
            action="category.updated",
            action_label="Category updated",
            module="TICKETS",
            target=category.name,
            severity="INFO",
        )

        messages.success(request, f"Category '{name}' updated.")

        return redirect("category_list")

    return redirect("category_list")


@login_required
def toggle_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(
        Category,
        id=category_id
    )

    category.is_active = not category.is_active
    category.save()

    log_activity(
        actor=request.user,
        action="category.status_toggled",
        action_label="Category status changed",
        module="TICKETS",
        target=category.name,
        severity="WARNING",
    )

    if category.is_active:
        messages.success(request, f"'{category.name}' marked as active.")
    else:
        messages.success(request, f"'{category.name}' marked as inactive.")

    return redirect("category_list")


@login_required
def delete_category(request, category_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    category = get_object_or_404(
        Category,
        id=category_id
    )

    category_name = category.name

    category.delete()

    log_activity(
        actor=request.user,
        action="category.deleted",
        action_label="Category deleted",
        module="TICKETS",
        target=category_name,
        severity="CRITICAL",
    )

    messages.success(request, f"Category '{category_name}' deleted.")

    return redirect("category_list")
