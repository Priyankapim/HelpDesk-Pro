from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import SupportRequest, SupportMessage
from departments.models import Department

from auditlogs.utils import log_activity

from .models import SupportRequest, SupportMessage


def _is_super_admin(user):
    return user.role == 'SUPER_ADMIN'


@login_required
def support_inbox(request):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    requests_qs = SupportRequest.objects.select_related('tenant').all()

    status = request.GET.get("status")

    if status:
        requests_qs = requests_qs.filter(status=status)

    context = {
        "requests": requests_qs,
        "total_requests": SupportRequest.objects.count(),
        "active_count": SupportRequest.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS', 'PENDING_USER']
        ).count(),
        "resolved_count": SupportRequest.objects.filter(status='RESOLVED').count(),
        "current_status": status or "",
        "status_choices": SupportRequest.STATUS_CHOICES,
    }

    return render(request, "tenant_support_inbox.html", context)


@login_required
def support_detail(request, request_id):

    if not _is_super_admin(request.user):
        return redirect('dashboard')

    support_request = get_object_or_404(
        SupportRequest.objects.select_related('tenant'),
        id=request_id
    )

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "update_status":

            old_status = support_request.status
            new_status = request.POST.get("status")

            support_request.status = new_status
            support_request.save()

            log_activity(
                actor=request.user,
                action="support.status_updated",
                action_label="Support request status updated",
                module="SUPPORT",
                target=support_request.ticket_number,
                severity="INFO",
                before={"status": old_status},
                after={"status": new_status},
            )

            messages.success(request, "Status updated.")

        elif action == "reply":

            message_text = request.POST.get("message", "").strip()

            if message_text:

                SupportMessage.objects.create(
                    request=support_request,
                    sender=request.user,
                    is_staff_reply=True,
                    message=message_text,
                )

                # Replying moves an OPEN request into IN_PROGRESS automatically.
                if support_request.status == 'OPEN':
                    support_request.status = 'IN_PROGRESS'
                    support_request.save()

                log_activity(
                    actor=request.user,
                    action="support.replied",
                    action_label="Replied to support request",
                    module="SUPPORT",
                    target=support_request.ticket_number,
                    severity="INFO",
                )

                messages.success(request, "Reply sent.")

        return redirect("support_detail", request_id=support_request.id)

    context = {
        "support_request": support_request,
        "conversation": support_request.messages.select_related('sender').all(),
        "status_choices": SupportRequest.STATUS_CHOICES,
    }

    return render(request, "tenant_support_detail.html", context)


def _is_tenant_admin(user):
    return user.role == 'ADMIN' and user.tenant is not None


@login_required
def my_support_requests(request):
    """
    Tenant ADMIN's own view of the support requests they've raised with
    NabiTech — list + a "New Request" modal that posts back to this
    same view.
    """

    if not _is_tenant_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")
        department_id = request.POST.get("department") or None

        if not subject or not description:
            messages.error(request, "Subject and description are required.")
            return redirect("my_support_requests")

        support_request = SupportRequest.objects.create(
            tenant=request.user.tenant,
            raised_by=request.user,
            subject=subject,
            description=description,
            priority=priority,
            department_id=department_id,
        )

        log_activity(
            actor=request.user,
            action="support.created",
            action_label="Support request created",
            module="SUPPORT",
            target=support_request.ticket_number,
            severity="INFO",
        )

        messages.success(request, f"Support request {support_request.ticket_number} submitted.")

        return redirect("my_support_requests")

    requests_qs = SupportRequest.objects.filter(tenant=request.user.tenant)

    status = request.GET.get("status")

    if status:
        requests_qs = requests_qs.filter(status=status)

    context = {
        "requests": requests_qs,
        "total_requests": SupportRequest.objects.filter(tenant=request.user.tenant).count(),
        "active_count": SupportRequest.objects.filter(
            tenant=request.user.tenant,
            status__in=['OPEN', 'IN_PROGRESS', 'PENDING_USER']
        ).count(),
        "resolved_count": SupportRequest.objects.filter(
            tenant=request.user.tenant, status='RESOLVED'
        ).count(),
        "current_status": status or "",
        "status_choices": SupportRequest.STATUS_CHOICES,
        "departments": Department.objects.filter(tenant__isnull=True, is_active=True).order_by('name'),
    }

    return render(request, "my_support_requests.html", context)


@login_required
def my_support_detail(request, request_id):
    """
    Tenant ADMIN's read + reply view of a single support request.
    Unlike the SuperAdmin's support_detail, there is NO status control
    here — only NabiTech can move a request through its lifecycle.
    """

    if not _is_tenant_admin(request.user):
        return redirect('dashboard')

    support_request = get_object_or_404(
        SupportRequest,
        id=request_id,
        tenant=request.user.tenant
    )

    if request.method == "POST":

        message_text = request.POST.get("message", "").strip()

        if message_text:

            SupportMessage.objects.create(
                request=support_request,
                sender=request.user,
                is_staff_reply=False,
                message=message_text,
            )

            # If NabiTech was waiting on the tenant and the tenant just
            # replied, move it back into an active state automatically.
            if support_request.status == 'PENDING_USER':
                support_request.status = 'IN_PROGRESS'
                support_request.save()

            log_activity(
                actor=request.user,
                action="support.replied",
                action_label="Tenant replied to support request",
                module="SUPPORT",
                target=support_request.ticket_number,
                severity="INFO",
            )

            messages.success(request, "Reply sent.")

        return redirect("my_support_detail", request_id=support_request.id)

    context = {
        "support_request": support_request,
        "conversation": support_request.messages.select_related('sender').all(),
    }

    return render(request, "my_support_detail.html", context)
