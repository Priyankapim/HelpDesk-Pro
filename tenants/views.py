from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from accounts.utils import generate_username
from auditlogs.utils import log_activity

from .forms import AcceptInviteForm
from .models import Tenant, Invite


def _is_super_admin(user):
    return user.role == 'SUPER_ADMIN'


def _send_invite_email(request, invite):
    """
    Sends the actual invite email via SMTP (uses EMAIL_HOST_* settings
    already configured in helpdesk/settings.py). Links to the public
    accept-invite page so the invited person can set their password
    and get a real account.
    """

    accept_url = request.build_absolute_uri(
        reverse('accept_invite', args=[invite.token])
    )

    subject = f"You're invited to join {invite.tenant.name} on ServiceDesk Pro"

    message = (
        f"Hi {invite.name},\n\n"
        f"You have been invited to join {invite.tenant.name} on ServiceDesk Pro "
        f"as a {invite.get_role_display()}.\n\n"
        f"Click here to activate your account:\n{accept_url}\n\n"
        f"This invite expires on {invite.expires_at.strftime('%B %d, %Y')}.\n\n"
        f"ServiceDesk Pro Team"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invite.email],
        fail_silently=False,
    )


@login_required
def tenant_list(request):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    tenants = Tenant.objects.all()

    search = request.GET.get("search")

    if search:
        tenants = tenants.filter(
            Q(name__icontains=search) | Q(slug__icontains=search)
        )

    plan = request.GET.get("plan")

    if plan:
        tenants = tenants.filter(plan=plan)

    context = {
        "tenants": tenants,
        "total_tenants": Tenant.objects.count(),
        "active_tenants": Tenant.objects.filter(is_active=True).count(),
        "trial_tenants": Tenant.objects.filter(plan='TRIAL').count(),
        "total_users": User.objects.filter(tenant__isnull=False).count(),
        "plans": Tenant.PLAN_CHOICES,
    }

    return render(request, "tenant_list.html", context)


@login_required
def create_tenant(request):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        if not name:
            messages.error(request, "Organization name is required.")
            return redirect("tenant_list")

        tenant = Tenant.objects.create(
            name=name,
            slug=request.POST.get("slug", "").strip(),
            plan=request.POST.get("plan", "TRIAL"),
            max_users=request.POST.get("max_users") or None,
            notes=request.POST.get("notes", ""),
        )

        log_activity(
            actor=request.user,
            action="tenant.created",
            action_label="Tenant created",
            module="TENANTS",
            target=tenant.name,
            severity="INFO",
            after={"plan": tenant.plan},
        )

        messages.success(request, f"Tenant '{tenant.name}' created.")

        return redirect("tenant_detail", tenant_id=tenant.id)

    return redirect("tenant_list")


@login_required
def tenant_detail(request, tenant_id):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    tenant = get_object_or_404(Tenant, id=tenant_id)

    invites = tenant.invites.all()

    context = {
        "tenant": tenant,
        "users": tenant.users.all(),
        "invites": invites,
        "pending_invites_count": invites.filter(status='PENDING').count(),
        "accepted_invites_count": invites.filter(status='ACCEPTED').count(),
        "onboarding_steps": tenant.onboarding_steps,
        "role_choices": Invite.ROLE_CHOICES,
    }

    return render(request, "tenant_detail.html", context)


@login_required
def send_invite(request, tenant_id):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    tenant = get_object_or_404(Tenant, id=tenant_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        role = request.POST.get("role", "EMPLOYEE")

        if not name or not email:
            messages.error(request, "Name and email are required.")
            return redirect("tenant_detail", tenant_id=tenant.id)

        invite = Invite.objects.create(
            tenant=tenant,
            name=name,
            email=email,
            role=role,
            invited_by=request.user,
            expires_at=timezone.now().date() + timedelta(days=7),
        )

        log_activity(
            actor=request.user,
            action="invite.created",
            action_label="Invite created",
            module="INVITES",
            target=invite.email,
            severity="INFO",
            after={"role": invite.role},
        )

        try:
            _send_invite_email(request, invite)
            messages.success(request, f"Invite sent to {invite.email}.")
        except Exception as e:
            messages.error(
                request,
                f"Invite was created, but the email could not be sent ({e}). "
                f"Check your EMAIL_HOST_USER / EMAIL_HOST_PASSWORD in settings.py."
            )

    return redirect("tenant_detail", tenant_id=tenant.id)


@login_required
def revoke_invite(request, invite_id):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    invite = get_object_or_404(Invite, id=invite_id)
    invite.status = 'REVOKED'
    invite.save()

    log_activity(
        actor=request.user,
        action="invite.revoked",
        action_label="Invite revoked",
        module="INVITES",
        target=invite.email,
        severity="WARNING",
    )

    messages.success(request, f"Invite for {invite.email} revoked.")

    return redirect("tenant_detail", tenant_id=invite.tenant_id)


@login_required
def resend_invite(request, invite_id):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    invite = get_object_or_404(Invite, id=invite_id)
    invite.status = 'PENDING'
    invite.expires_at = timezone.now().date() + timedelta(days=7)
    invite.save()

    log_activity(
        actor=request.user,
        action="invite.resent",
        action_label="Invite resent",
        module="INVITES",
        target=invite.email,
        severity="INFO",
    )

    try:
        _send_invite_email(request, invite)
        messages.success(request, f"Invite for {invite.email} resent.")
    except Exception as e:
        messages.error(
            request,
            f"Invite was updated, but the email could not be resent ({e})."
        )

    return redirect("tenant_detail", tenant_id=invite.tenant_id)


# =====================================================
# Public Accept-Invite page (no login required — this
# is where a brand new user actually gets an account)
# =====================================================

def accept_invite(request, token):

    try:
        invite = Invite.objects.select_related('tenant').get(token=token)
    except Invite.DoesNotExist:
        messages.error(request, "Invalid invitation link.")
        return redirect("login")

    if invite.status == "ACCEPTED":
        messages.info(request, "This invitation has already been accepted. Please login.")
        return redirect("login")

    elif invite.status == "REVOKED":
        messages.error(request, "This invitation has been revoked.")
        return redirect("login")

    elif invite.is_expired:
        invite.status = "EXPIRED"
        invite.save()
        messages.error(request, "This invitation has expired. Please contact your administrator.")
        return redirect("login")

    form = AcceptInviteForm()

    if request.method == "POST":

        form = AcceptInviteForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data["password"]
            confirm = form.cleaned_data["confirm_password"]

            if password != confirm:
                messages.error(request, "Passwords do not match.")

            elif User.objects.filter(email=invite.email).exists():
                messages.error(request, "An account already exists with this email.")
                return redirect("login")

            else:

                name_parts = invite.name.strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""

                User.objects.create_user(
                    username=generate_username(invite.email),
                    email=invite.email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=invite.role,
                    tenant=invite.tenant,
                    is_active=True,
                )

                invite.status = "ACCEPTED"
                invite.accepted_at = timezone.now()
                invite.save()

                log_activity(
                    actor=None,
                    action="invite.accepted",
                    action_label="Invite accepted",
                    module="INVITES",
                    target=invite.email,
                    severity="INFO",
                    after={"role": invite.role, "tenant": invite.tenant.name},
                )

                messages.success(request, "Your account has been activated successfully. Please sign in.")

                return redirect(f"{reverse('login')}?email={invite.email}")

    return render(
        request,
        "accept_invite.html",
        {
            "form": form,
            "invite": invite,
        }
    )
