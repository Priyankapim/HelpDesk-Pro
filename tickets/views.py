
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

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
def ticket_detail(request, ticket_id):

    ticket = get_object_or_404(
        Ticket,
        id=ticket_id
    )

    return render(
        request,
        'tickets/ticket_detail.html',
        {'ticket': ticket}
    )



@login_required
def all_tickets(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    tickets = Ticket.objects.all().order_by('-created_at')

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

    agents = User.objects.filter(
        role='AGENT'
    )

    comments = ticket.comments.all().order_by('-created_at')

    if request.method == 'POST':

        agent_id = request.POST.get('assigned_to')

        if agent_id:
            ticket.assigned_to_id = agent_id

        status = request.POST.get('status')

        if status:
            ticket.status = status

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















