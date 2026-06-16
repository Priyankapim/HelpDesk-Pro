from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from notifications.utils import send_ticket_email
from .forms import TicketForm
from .models import Ticket, TicketComment
from accounts.models import User




@login_required
def create_ticket(request):

    if request.method == "POST":

        form = TicketForm(request.POST)

        if form.is_valid():

            ticket = form.save(commit=False)

            ticket.created_by = request.user

            ticket.save()


            send_ticket_email(

                subject="Ticket Created Successfully",

                message=f"""
            Hello {request.user.first_name or request.user.email},
6
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
    ).order_by('-created_at')

    return render(
        request,
        'tickets/my_tickets.html',
        {'tickets': tickets}
    )


@login_required
def all_tickets(request):

    if request.user.role not in [
        'ADMIN',
        'SUPER_ADMIN'
    ]:
        return redirect('dashboard')

    tickets = Ticket.objects.all().order_by(
        '-created_at'
    )

    return render(
        request,
        'tickets/all_tickets.html',
        {'tickets': tickets}
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



















