from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from notifications.utils import send_ticket_email
from .forms import TicketForm
from .models import Ticket, TicketComment, Notification
from accounts.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.urls import reverse
from departments.models import Department
from django.core.paginator import Paginator





@login_required
def create_ticket(request):

    if request.method == "POST":

        form = TicketForm(request.POST)

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

            return redirect('dashboard')

    else:

        form = TicketForm()

    return render(
        request,
        'tickets/create_ticket.html',
        {'form': form}
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

    sla_breached = Ticket.objects.filter(
        created_by=request.user,
        status="Open"
    ).count()

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
        request,
        "tickets/my_tickets.html",
        context,
    )

from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def all_tickets(request):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        return redirect("dashboard")

    tickets = Ticket.objects.select_related(
        "department",
        "created_by",
        "assigned_to"
    ).order_by("-created_at")


    # ---------------- Search ----------------

    search = request.GET.get("search")

    if search:

        tickets = tickets.filter(

            Q(ticket_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(created_by__email__icontains=search)

        )


    # ---------------- Status ----------------

    status = request.GET.get("status")

    if status:

        tickets = tickets.filter(status=status)


    # ---------------- Priority ----------------

    priority = request.GET.get("priority")

    if priority:

        tickets = tickets.filter(priority=priority)


    # ---------------- Department ----------------

    department = request.GET.get("department")

    if department:

        tickets = tickets.filter(department_id=department)


    # ---------------- Assigned ----------------

    assigned = request.GET.get("assigned")

    if assigned == "yes":

        tickets = tickets.filter(
            assigned_to__isnull=False
        )

    elif assigned == "no":

        tickets = tickets.filter(
            assigned_to__isnull=True
        )


    paginator = Paginator(tickets,10)

    page=request.GET.get("page")

    tickets=paginator.get_page(page)


    context={

        "tickets":tickets,

        "search":search,

        "selected_status":status,

        "selected_priority":priority,

        "selected_department":department,

        "selected_assigned":assigned,

        "status_choices":Ticket.STATUS_CHOICES,

        "priority_choices":Ticket.PRIORITY_CHOICES,

        "departments":Department.objects.all(),

        "total_tickets":Ticket.objects.count(),

        "open_tickets":Ticket.objects.filter(status="Open").count(),

        "resolved_tickets":Ticket.objects.filter(status="Resolved").count(),

        "unassigned":Ticket.objects.filter(assigned_to__isnull=True).count(),

    }

    return render(
        request,
        "tickets/all_tickets.html",
        context,
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
                request.user.role in [
            'ADMIN',
            'SUPER_ADMIN'
        ]
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




        comment_text = request.POST.get('comment')

        if comment_text:
            TicketComment.objects.create(
                ticket=ticket,
                user=request.user,
                comment=comment_text
            )

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

        request,
        'tickets/assigned_tickets.html',
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

        # =====================================================
        # Tickets
        # =====================================================

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

        else:   # ADMIN / SUPER_ADMIN

            tickets = Ticket.objects.filter(
                ticket_filter
            ).distinct()[:5]

        for ticket in tickets:

            results.append({

                "type": "ticket",

                "title": ticket.ticket_number,

                "subtitle": ticket.title,

                "extra": f"{ticket.department.name} • {ticket.status}",

                "url": reverse("ticket_detail", args=[ticket.id])

            })

        # =====================================================
        # Users (Only Admin & Super Admin)
        # =====================================================

        if role in ["ADMIN", "SUPER_ADMIN"]:

            users = User.objects.filter(

                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)

            )[:5]

            for user in users:

                results.append({

                    "type": "user",

                    "title": f"{user.first_name} {user.last_name}",

                    "subtitle": user.email,

                    "extra": user.role,

                    "url": reverse("users_list")

                })

        # =====================================================
        # Departments
        # =====================================================

        departments = Department.objects.filter(
            name__icontains=query
        )[:5]

        for dept in departments:

            results.append({

                "type": "department",

                "title": dept.name,

                "subtitle": "Department",

                "extra": dept.description if dept.description else "",

                "url": reverse("department_list")

            })

    return JsonResponse(results, safe=False)













