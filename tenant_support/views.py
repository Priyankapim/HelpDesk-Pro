from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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


@login_required
def raise_support_request(request):
    """
    Lets a tenant ADMIN raise a support request to NabiTech (SuperAdmin).
    Not shown in the reference screenshots, but needed so the inbox
    actually has real data flowing into it.
    """

    if request.user.role != 'ADMIN' or not request.user.tenant:
        return redirect('dashboard')

    if request.method == "POST":

        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority = request.POST.get("priority", "MEDIUM")

        if not subject or not description:
            messages.error(request, "Subject and description are required.")
            return redirect("raise_support_request")

        support_request = SupportRequest.objects.create(
            tenant=request.user.tenant,
            raised_by=request.user,
            subject=subject,
            description=description,
            priority=priority,
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

        return redirect("dashboard")

    return render(request, "raise_support_request.html")
