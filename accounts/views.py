from datetime import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from auditlogs.utils import log_activity
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
from .models import Invitation
from .forms import InvitationForm
from .utils import generate_username
from .utils import send_invitation_email

from django.db.models import Q



from .forms import AcceptInvitationForm


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user_obj = User.objects.filter(
            email=email
        ).first()

        if not user_obj:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")


        # Account inactive

        if not user_obj.is_active:

            messages.error(
                request,
                "Your account is inactive. Please contact Administrator."
            )

            return redirect("login")


        # Account locked

        if user_obj.is_locked:

            messages.error(
                request,
                "Your account has been locked. Please contact Administrator."
            )

            return redirect("login")


        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user:

            login(request, user)

            return redirect("dashboard")


        messages.error(
            request,
            "Invalid email or password."
        )

        return redirect("login")


    return render(
        request,
        "login.html",
        {
            "email": request.GET.get("email", "")
        }
    )


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


from django.db.models import Q


@login_required
def users_list(request):

    users = User.objects.all().order_by("first_name")

    # Non-super-admins only ever see users from their own tenant.
    # SUPER_ADMIN sees every tenant's users.
    if request.user.role != 'SUPER_ADMIN':
        users = users.filter(tenant=request.user.tenant)



    # =======================
    # Search
    # =======================

    search = request.GET.get("search")

    if search:

        users = users.filter(

            Q(first_name__icontains=search) |

            Q(last_name__icontains=search) |

            Q(email__icontains=search) |

            Q(username__icontains=search)

        )

    # =======================
    # Role Filter
    # =======================

    role = request.GET.get("role")

    if role:

        users = users.filter(
            role=role
        )

    # =======================
    # Status Filter
    # =======================

    status = request.GET.get("status")

    if status == "active":

        users = users.filter(
            is_active=True
        )

    elif status == "inactive":

        users = users.filter(
            is_active=False
        )

    # =======================
    # Summary
    # =======================

    total_users = User.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    inactive_users = User.objects.filter(
        is_active=False
    ).count()

    # Django me lock concept nahi hai
    locked_users = 0

    context = {

        "users": users,

        "total_users": total_users,

        "active_users": active_users,

        "inactive_users": inactive_users,

        "locked_users": locked_users,

    }

    return render(

        request,

        "users_list.html",

        context

    )

@login_required
def edit_user(request, user_id):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        return redirect("dashboard")

    user_obj = get_object_or_404(
        User,
        id=user_id
    )

    if request.method == "POST":
        old_role = user_obj.role
        # Role
        user_obj.role = request.POST.get("role")

        # Department
        department_id = request.POST.get("department")

        if department_id:
            user_obj.department_id = department_id
        else:
            user_obj.department = None

        # Active
        user_obj.is_active = "is_active" in request.POST

        # Locked
        user_obj.is_locked = "is_locked" in request.POST

        # Save
        user_obj.save()

        messages.success(
            request,
            "User updated successfully."
        )

        log_activity(
            actor=request.user,
            action="user.role_updated",
            action_label="User role updated",
            module="USERS",
            target=user_obj.email,
            severity="INFO",
            before={"role": old_role},
            after={"role": user_obj.role},
        )

        return redirect("users_list")

    context = {

        "user_obj": user_obj,

        "departments": Department.objects.all(),

    }

    return render(

        request,

        "edit_user.html",

        context,

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

                log_activity(
                    actor=request.user,
                    action="user.password_changed",
                    action_label="Password changed",
                    module="CONFIG",
                    target=request.user.email,
                    severity="WARNING",
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





@login_required
def invitation_list(request):

    invitations = Invitation.objects.all()

    # Search
    search = request.GET.get("search")

    if search:

        invitations = invitations.filter(

            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)

        )

    # Status Filter
    status = request.GET.get("status")

    if status:

        invitations = invitations.filter(
            status=status
        )

    invitations = invitations.order_by("-created_at")

    context = {

        "invitations": invitations,

        "pending_count": Invitation.objects.filter(
            status="PENDING"
        ).count(),

        "accepted_count": Invitation.objects.filter(
            status="ACCEPTED"
        ).count(),

        "expired_count": Invitation.objects.filter(
            status="EXPIRED"
        ).count(),

        "revoked_count": Invitation.objects.filter(
            status="REVOKED"
        ).count(),

    }

    return render(
        request,
        "invitation_list.html",
        context
    )

@login_required
def invite_user(request):

    if request.method == "POST":

        form = InvitationForm(request.POST)

        if form.is_valid():
            invitation = form.save(commit=False)

            invitation.invited_by = request.user

            invitation.save()

            send_invitation_email(
                invitation
            )

            log_activity(
                actor=request.user,
                action="invite.created",
                action_label="Invite created",
                module="INVITES",
                target=invitation.email,
                severity="INFO",
                after={"role": invitation.role, "department": str(invitation.department)},
            )

            messages.success(
                request,
                "Invitation created successfully."
            )

            return redirect("invitation_list")

    else:

        form = InvitationForm()

    return render(
        request,
        "invite_user.html",
        {
            "form": form
        }
    )



def accept_invitation(request, token):

    try:

        invitation = Invitation.objects.get(
            token=token
        )

    except Invitation.DoesNotExist:

        messages.error(
            request,
            "Invalid invitation."
        )

        return redirect("login")

    if invitation.status == "ACCEPTED":

        messages.info(
            request,
            "This invitation has already been accepted. Please login."
        )

        return redirect("login")

    elif invitation.status == "REVOKED":

        messages.error(
            request,
            "This invitation has been revoked."
        )

        return redirect("login")

    elif invitation.status == "EXPIRED":

        messages.error(
            request,
            "This invitation has expired."
        )

        return redirect("login")


    if timezone.now() > invitation.expires_at:

        invitation.status = "EXPIRED"

        invitation.save()

        messages.error(

            request,

            "Your invitation has expired. Please contact your administrator."

        )

        return redirect("login")


    form = AcceptInvitationForm()


    if request.method == "POST":

        form = AcceptInvitationForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data["password"]

            confirm = form.cleaned_data["confirm_password"]


            if password != confirm:

                messages.error(
                    request,
                    "Passwords do not match."
                )


            else:

                # Check if account already exists

                if User.objects.filter(

                        email=invitation.email

                ).exists():
                    messages.error(

                        request,

                        "An account already exists with this email."

                    )

                    return redirect("login")

                user = User.objects.create_user(

                    username=generate_username(
                        invitation.email
                    ),

                    email=invitation.email,

                    password=password,

                    first_name=invitation.first_name,

                    last_name=invitation.last_name,

                    role=invitation.role,

                    department=invitation.department,

                    is_active=True,

                )

                invitation.status = "ACCEPTED"

                invitation.save()

                log_activity(
                    actor=None,
                    action="invite.accepted",
                    action_label="Invite accepted",
                    module="INVITES",
                    target=invitation.email,
                    severity="INFO",
                    after={"role": invitation.role},
                )

                messages.success(
                    request,
                    "Your account has been activated successfully. Please sign in."
                )

                return redirect(
                    f"{reverse('login')}?email={invitation.email}"
                )


    return render(

        request,

        "accept_invitation.html",

        {

            "form": form,

            "invitation": invitation,

        }

    )



@login_required
def revoke_invitation(request, invitation_id):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:

        return redirect("dashboard")

    invitation = get_object_or_404(

        Invitation,

        id=invitation_id

    )

    if invitation.status == "ACCEPTED":

        messages.error(

            request,

            "Accepted invitations cannot be revoked."

        )

        return redirect("invitation_list")

    invitation.status = "REVOKED"

    invitation.save()

    log_activity(
        actor=request.user,
        action="invite.revoked",
        action_label="Invite revoked",
        module="INVITES",
        target=invitation.email,
        severity="WARNING",
    )

    messages.success(

        request,

        "Invitation revoked successfully."

    )

    return redirect("invitation_list")


@login_required
def delete_invitation(request, invitation_id):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        return redirect("dashboard")

    invitation = get_object_or_404(
        Invitation,
        id=invitation_id
    )

    invitation_email = invitation.email

    invitation.delete()

    log_activity(
        actor=request.user,
        action="invite.deleted",
        action_label="Invite deleted",
        module="INVITES",
        target=invitation_email,
        severity="WARNING",
    )

    messages.success(
        request,
        "Invitation deleted successfully."
    )

    return redirect("invitation_list")


@login_required
def resend_invitation(request, invitation_id):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        return redirect("dashboard")

    invitation = get_object_or_404(
        Invitation,
        id=invitation_id
    )

    invitation.status = "PENDING"

    invitation.expires_at = timezone.now() + timedelta(days=7)

    invitation.save()

    send_invitation_email(
        invitation
    )

    log_activity(
        actor=request.user,
        action="invite.resent",
        action_label="Invite resent",
        module="INVITES",
        target=invitation.email,
        severity="INFO",
    )

    messages.success(
        request,
        "Invitation resent successfully."
    )

    return redirect("invitation_list")