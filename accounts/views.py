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
from .models import SecuritySettings, LoginActivity, UserSession
from tenants.models import Tenant
from tenant_support.models import SupportRequest
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from notifications.utils import send_ticket_email
from .forms import AcceptInvitationForm
from .utils import parse_user_agent


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        ip_address = get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

        security_settings = SecuritySettings.get_settings()

        user_obj = User.objects.filter(
            email=email
        ).first()

        if not user_obj:

            LoginActivity.objects.create(
                user=None,
                email_attempted=email or "",
                ip_address=ip_address,
                user_agent=user_agent,
                status="FAILED"
            )

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

        # Tenant suspended — blocks everyone except the platform's own
        # Super Admin (who has no tenant)

        if user_obj.tenant_id and not user_obj.tenant.is_active:
            messages.error(
                request,
                "Your organization's account has been suspended. "
                "Please contact support."
            )

            return redirect("login")

        # Account locked - check if the lockout duration has already passed

        if user_obj.is_locked:

            unlock_due = None

            if user_obj.locked_at:
                unlock_due = user_obj.locked_at + timedelta(
                    minutes=security_settings.lockout_duration_minutes
                )

            if unlock_due and timezone.now() >= unlock_due:

                # Auto-unlock, give the user a fresh set of attempts
                user_obj.is_locked = False
                user_obj.locked_at = None
                user_obj.failed_login_attempts = 0
                user_obj.save(update_fields=[
                    "is_locked", "locked_at", "failed_login_attempts"
                ])

            else:

                LoginActivity.objects.create(
                    user=user_obj,
                    email_attempted=email,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    status="LOCKED"
                )

                messages.error(
                    request,
                    f"Your account is locked due to too many failed attempts. "
                    f"Try again after {security_settings.lockout_duration_minutes} minutes, "
                    f"or contact an Administrator."
                )

                return redirect("login")


        user = authenticate(
            request,
            email=email,
            password=password
        )

        if user:

            user.failed_login_attempts = 0
            user.is_locked = False
            user.locked_at = None
            user.save(update_fields=[
                "failed_login_attempts", "is_locked", "locked_at"
            ])

            login(request, user)

            LoginActivity.objects.create(
                user=user,
                email_attempted=email,
                ip_address=ip_address,
                user_agent=user_agent,
                status="SUCCESS"
            )

            if not request.session.session_key:
                request.session.save()

            UserSession.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    "user": user,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            )

            return redirect("dashboard")


        # Wrong password - increment failed attempts

        user_obj.failed_login_attempts += 1

        if user_obj.failed_login_attempts >= security_settings.max_failed_attempts:

            user_obj.is_locked = True
            user_obj.locked_at = timezone.now()
            user_obj.save(update_fields=[
                "failed_login_attempts", "is_locked", "locked_at"
            ])

            LoginActivity.objects.create(
                user=user_obj,
                email_attempted=email,
                ip_address=ip_address,
                user_agent=user_agent,
                status="LOCKED"
            )

            messages.error(
                request,
                f"Your account has been locked after "
                f"{security_settings.max_failed_attempts} failed attempts. "
                f"Try again after {security_settings.lockout_duration_minutes} minutes."
            )

            return redirect("login")

        user_obj.save(update_fields=["failed_login_attempts"])

        LoginActivity.objects.create(
            user=user_obj,
            email_attempted=email,
            ip_address=ip_address,
            user_agent=user_agent,
            status="FAILED"
        )

        remaining = security_settings.max_failed_attempts - user_obj.failed_login_attempts

        messages.error(
            request,
            f"Invalid email or password. {remaining} attempt(s) remaining before lockout."
        )

        return redirect("login")


    return render(
        request,
        "login.html",
        {
            "email": request.GET.get("email", "")
        }
    )

def _super_admin_dashboard(request):
    """
    Platform-level dashboard for SUPER_ADMIN — shows tenant and
    Support Request stats instead of any single tenant's internal
    ticket data.
    """
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()

    requests_qs = SupportRequest.objects.all()

    total_requests = requests_qs.count()

    open_requests = requests_qs.filter(
        status__in=['OPEN', 'IN_PROGRESS', 'PENDING_USER']
    ).count()

    resolved_requests = requests_qs.filter(
        status__in=['RESOLVED', 'CLOSED']
    ).count()

    critical_requests = requests_qs.filter(
        priority='CRITICAL'
    ).count()

    status_labels = [
        'Open',
        'Progress',
       #'Pending',
        'Resolved',
        'Closed'
    ]

    status_data = [
        requests_qs.filter(status='OPEN').count(),
        requests_qs.filter(status='IN_PROGRESS').count(),
        #requests_qs.filter(status='PENDING_USER').count(),
        requests_qs.filter(status='RESOLVED').count(),
        requests_qs.filter(status='CLOSED').count(),
    ]

    priority_labels = ['Low', 'Medium', 'High', 'Critical']

    priority_data = [
        requests_qs.filter(priority='LOW').count(),
        requests_qs.filter(priority='MEDIUM').count(),
        requests_qs.filter(priority='HIGH').count(),
        requests_qs.filter(priority='CRITICAL').count(),
    ]

    department_counts = requests_qs.values(
        'department__name'
    ).annotate(count=Count('id')).order_by('-count')

    department_labels = [
        (row['department__name'] or 'General') for row in department_counts
    ]
    department_data = [row['count'] for row in department_counts]

    recent_requests = requests_qs.select_related(
        'tenant'
    ).order_by('-created_at')[:6]

    recent_tenants = Tenant.objects.order_by('-created_at')[:5]

    context = {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_requests": total_requests,
        "open_requests": open_requests,
        "resolved_requests": resolved_requests,
        "critical_requests": critical_requests,
        "status_labels": status_labels,
        "status_data": status_data,
        "priority_labels": priority_labels,
        "priority_data": priority_data,
        "department_labels": department_labels,
        "department_data": department_data,
        "recent_requests": recent_requests,
        "recent_tenants": recent_tenants,
    }

    return render(
        request,
        "dashboard/super_admin_dashboard.html",
        context
    )

@login_required
def dashboard_view(request):
    if request.user.role == "SUPER_ADMIN":
        return _super_admin_dashboard(request)

    days_filter = request.GET.get("days", "30")
    department_filter = request.GET.get("department", "")

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

    elif request.user.role == "ADMIN":
        tickets = Ticket.objects.filter(
            tenant_id=request.user.tenant_id
        )



    else:
        # AGENT/EMPLOYEE fallback (should not normally reach here)
        tickets = Ticket.objects.none()

    if department_filter:
        tickets = tickets.filter(department_id=department_filter)

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
        "selected_department": department_filter,
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

    if request.session.session_key:
        UserSession.objects.filter(
            session_key=request.session.session_key
        ).delete()

    logout(request)
    return redirect('login')





@login_required
def users_list(request):

    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    users = User.objects.filter(
        tenant=request.user.tenant
    ).order_by("first_name")



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
    # Summary (tenant-scoped, not global)
    # =======================

    tenant_users = User.objects.filter(tenant=request.user.tenant)

    total_users = tenant_users.count()

    active_users = tenant_users.filter(
        is_active=True
    ).count()

    inactive_users = tenant_users.filter(
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

    if request.user.role == "EMPLOYEE":
        tickets = Ticket.objects.filter(created_by=request.user)
    elif request.user.role == "AGENT":
        tickets = Ticket.objects.filter(assigned_to=request.user)
    elif request.user.role == "ADMIN":
        tickets = Ticket.objects.filter(tenant_id=request.user.tenant_id)
    else:
        # SUPER_ADMIN: does not own tenant tickets
        tickets = Ticket.objects.none()

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


def forgot_password_view(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip()

        user = User.objects.filter(email__iexact=email).first()

        if user:

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_link = request.build_absolute_uri(
                reverse("reset_password", args=[uid, token])
            )

            email_message = (
                f"Hello {user.first_name or user.email},\n\n"
                f"We received a request to reset your ServiceDesk Pro password.\n\n"
                f"Click the link below to set a new password:\n{reset_link}\n\n"
                f"If you didn't request this, you can safely ignore this email - "
                f"your password will not be changed.\n\n"
                f"This link will stop working once you use it or change your password."
            )

            try:
                send_ticket_email(
                    subject="Reset your ServiceDesk Pro password",
                    message=email_message,
                    recipient=user.email
                )
            except Exception:
                pass

        # Always show the same message whether or not the email exists,
        # so people can't use this form to check who has an account.
        messages.success(
            request,
            "If an account exists with that email, a password reset link has been sent."
        )

        return redirect("login")

    return render(
        request,
        "forgot_password.html"
    )


def reset_password_view(request, uidb64, token):

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    token_valid = (
        user is not None
        and default_token_generator.check_token(user, token)
    )

    if not token_valid:

        messages.error(
            request,
            "This password reset link is invalid or has expired. Please request a new one."
        )

        return redirect("forgot_password")

    if request.method == "POST":

        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if new_password != confirm_password:

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

            user.set_password(new_password)
            user.failed_login_attempts = 0
            user.is_locked = False
            user.locked_at = None
            user.save()

            log_activity(
                actor=user,
                action="user.password_reset",
                action_label="Password reset via email link",
                module="CONFIG",
                target=user.email,
                severity="WARNING",
            )

            messages.success(
                request,
                "Your password has been reset successfully. Please login with your new password."
            )

            return redirect("login")

    return render(
        request,
        "reset_password.html",
        {
            "uidb64": uidb64,
            "token": token
        }
    )





@login_required
def invitation_list(request):

    invitations = Invitation.objects.filter(
        invited_by__tenant=request.user.tenant
    )

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

    tenant_invitations = Invitation.objects.filter(
        invited_by__tenant=request.user.tenant
    )

    context = {

        "invitations": invitations,

        "pending_count": tenant_invitations.filter(
            status="PENDING"
        ).count(),

        "accepted_count": tenant_invitations.filter(
            status="ACCEPTED"
        ).count(),

        "expired_count": tenant_invitations.filter(
            status="EXPIRED"
        ).count(),

        "revoked_count": tenant_invitations.filter(
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
                after={"role": invitation.role},
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
                    username=generate_username(invitation.email),
                    email=invitation.email,
                    password=password,
                    first_name=invitation.first_name,
                    last_name=invitation.last_name,
                    role=invitation.role,
                    department=invitation.department,
                    tenant=invitation.invited_by.tenant,
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



@login_required
def security_settings_view(request):

    security_settings = SecuritySettings.get_settings()

    # Drop stale UserSession rows whose real Django session has expired/gone
    from django.contrib.sessions.models import Session

    live_keys = set(
        Session.objects.filter(
            expire_date__gte=timezone.now()
        ).values_list("session_key", flat=True)
    )

    UserSession.objects.filter(user=request.user).exclude(
        session_key__in=live_keys
    ).delete()

    active_sessions = UserSession.objects.filter(
        user=request.user
    ).order_by("-last_activity")

    for s in active_sessions:
        s.device_label = parse_user_agent(s.user_agent)

    login_activity = LoginActivity.objects.filter(
        user=request.user
    ).order_by("-created_at")[:20]

    for entry in login_activity:
        entry.device_label = parse_user_agent(entry.user_agent)

    context = {
        "security_settings": security_settings,
        "active_sessions": active_sessions,
        "current_session_key": request.session.session_key,
        "login_activity": login_activity,
        "can_edit_lockout_policy": request.user.role in ["ADMIN", "SUPER_ADMIN"],
    }

    return render(
        request,
        "security_settings.html",
        context
    )


@login_required
def update_security_settings(request):

    if request.user.role not in ["ADMIN", "SUPER_ADMIN"]:
        messages.error(request, "You don't have permission to change this.")
        return redirect("security_settings")

    if request.method == "POST":

        try:
            max_attempts = int(request.POST.get("max_failed_attempts", 5))
            duration = int(request.POST.get("lockout_duration_minutes", 15))

        except ValueError:
            messages.error(request, "Please enter valid numbers.")
            return redirect("security_settings")

        if max_attempts < 1 or duration < 1:
            messages.error(request, "Values must be at least 1.")
            return redirect("security_settings")

        security_settings = SecuritySettings.get_settings()
        security_settings.max_failed_attempts = max_attempts
        security_settings.lockout_duration_minutes = duration
        security_settings.save()

        messages.success(request, "Security settings updated.")

    return redirect("security_settings")


@login_required
def logout_other_sessions(request):

    if request.session.session_key:

        UserSession.objects.filter(
            user=request.user
        ).exclude(
            session_key=request.session.session_key
        ).delete()

        from django.contrib.sessions.models import Session

        # Delete every real session for this user except the current one
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            data = session.get_decoded()
            if (
                str(data.get("_auth_user_id")) == str(request.user.id)
                and session.session_key != request.session.session_key
            ):
                session.delete()

    messages.success(request, "Logged out from all other devices.")

    return redirect("security_settings")


@login_required
def logout_session(request, session_key):

    user_session = UserSession.objects.filter(
        user=request.user,
        session_key=session_key
    ).first()

    if not user_session:
        messages.error(request, "Session not found.")
        return redirect("security_settings")

    if session_key == request.session.session_key:
        messages.error(request, "Use Logout to end your current session.")
        return redirect("security_settings")

    from django.contrib.sessions.models import Session

    Session.objects.filter(session_key=session_key).delete()
    user_session.delete()

    messages.success(request, "That session has been logged out.")

    return redirect("security_settings")

