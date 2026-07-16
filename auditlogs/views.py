import csv

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from .models import AuditLog


def _apply_filters(request, logs):

    # =======================
    # Search (action, target, actor)
    # =======================

    search = request.GET.get("search")

    if search:
        from django.db.models import Q

        logs = logs.filter(
            Q(action_label__icontains=search) |
            Q(target__icontains=search) |
            Q(actor__first_name__icontains=search) |
            Q(actor__last_name__icontains=search) |
            Q(actor__email__icontains=search)
        )

    # =======================
    # Module Filter
    # =======================

    module = request.GET.get("module")

    if module:
        logs = logs.filter(module=module)

    # =======================
    # Severity Filter
    # =======================

    severity = request.GET.get("severity")

    if severity:
        logs = logs.filter(severity=severity)

    # =======================
    # User Filter
    # =======================

    user_id = request.GET.get("user")

    if user_id:
        logs = logs.filter(actor_id=user_id)

    # =======================
    # Single Date Filter
    # =======================

    date = request.GET.get("date")

    if date:
        logs = logs.filter(created_at__date=date)

    return logs


@login_required
def audit_log_list(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('actor').all()

    logs = _apply_filters(request, logs)

    # =======================
    # Summary Cards
    # =======================

    all_logs = AuditLog.objects.all()

    total_events = all_logs.count()

    last_24h = all_logs.filter(
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).count()

    info_count = all_logs.filter(severity='INFO').count()
    warning_count = all_logs.filter(severity='WARNING').count()
    critical_count = all_logs.filter(severity='CRITICAL').count()

    context = {
        "logs": logs,
        "total_events": total_events,
        "last_24h": last_24h,
        "info_count": info_count,
        "warning_count": warning_count,
        "critical_count": critical_count,
        "modules": AuditLog.MODULE_CHOICES,
        "severities": AuditLog.SEVERITY_CHOICES,
        "actors": User.objects.filter(
            audit_logs__isnull=False
        ).distinct().order_by('first_name'),
    }

    return render(
        request,
        "audit_logs.html",
        context
    )


@login_required
def audit_log_export_csv(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    logs = AuditLog.objects.select_related('actor').all()
    logs = _apply_filters(request, logs)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Time', 'Actor', 'Action', 'Module', 'Target', 'Severity'
    ])

    for log in logs:
        writer.writerow([
            log.created_at.strftime('%d-%m-%Y %I:%M %p'),
            log.actor_name,
            log.action_label,
            log.get_module_display(),
            log.target,
            log.get_severity_display(),
        ])

    return response
