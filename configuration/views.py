from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from departments.models import Department
from auditlogs.utils import log_activity

from .models import WorkingHours, Holiday, EscalationRule, EmailTemplate


def _is_admin(user):
    return user.role == 'ADMIN'


@login_required
def config_home(request):

    if not _is_admin(request.user):
        return redirect('dashboard')

    tenant = request.user.tenant

    for day_code, _label in WorkingHours.DAY_CHOICES:
        WorkingHours.objects.get_or_create(tenant=tenant, day=day_code)

    context = {
        "departments": Department.objects.filter(tenant=tenant).order_by('name'),
        "working_hours": WorkingHours.objects.filter(tenant=tenant),
        "holidays": Holiday.objects.filter(tenant=tenant),
        "escalation_rules": EscalationRule.objects.filter(tenant=tenant).select_related('department'),
        "templates": EmailTemplate.objects.filter(tenant=tenant),
        "selected_department_id": request.GET.get("department", ""),
    }

    return render(request, "admin_config.html", context)


@login_required
def save_sla_rules(request, department_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    department = get_object_or_404(Department, id=department_id, tenant=request.user.tenant)

    if request.method == "POST":

        department.sla_critical = request.POST.get("sla_critical") or department.sla_critical
        department.sla_high = request.POST.get("sla_high") or department.sla_high
        department.sla_medium = request.POST.get("sla_medium") or department.sla_medium
        department.sla_low = request.POST.get("sla_low") or department.sla_low

        department.save()

        log_activity(
            actor=request.user,
            action="config.sla_rules_updated",
            action_label="SLA rules updated",
            module="CONFIG",
            target=department.name,
            severity="INFO",
            after={
                "critical": department.sla_critical,
                "high": department.sla_high,
                "medium": department.sla_medium,
                "low": department.sla_low,
            },
        )

        messages.success(request, f"SLA rules updated for {department.name}.")

    return redirect(f"/configuration/?department={department.id}")


@login_required
def save_working_hours(request):

    if not _is_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        for day_code, _label in WorkingHours.DAY_CHOICES:

            wh, _created = WorkingHours.objects.get_or_create(
                tenant=request.user.tenant,
                day=day_code
            )

            wh.is_working = f"is_working_{day_code}" in request.POST

            start = request.POST.get(f"start_{day_code}")
            end = request.POST.get(f"end_{day_code}")

            if start:
                wh.start_time = start

            if end:
                wh.end_time = end

            wh.save()

        log_activity(
            actor=request.user,
            action="config.working_hours_updated",
            action_label="Working hours updated",
            module="CONFIG",
            target="Working Hours Schedule",
            severity="INFO",
        )

        messages.success(request, "Working hours updated.")

    return redirect("/configuration/?tab=hours")


@login_required
def add_holiday(request):

    if not _is_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        date = request.POST.get("date")
        recurring = "recurring" in request.POST

        if not name or not date:
            messages.error(request, "Holiday name and date are required.")
            return redirect("/configuration/?tab=holidays")

        Holiday.objects.create(
            tenant=request.user.tenant,
            name=name,
            date=date,
            recurring=recurring,
        )

        log_activity(
            actor=request.user,
            action="config.holiday_created",
            action_label="Holiday added",
            module="CONFIG",
            target=name,
            severity="INFO",
        )

        messages.success(request, f"Holiday '{name}' added.")

    return redirect("/configuration/?tab=holidays")


@login_required
def delete_holiday(request, holiday_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    holiday = get_object_or_404(Holiday, id=holiday_id, tenant=request.user.tenant)
    holiday_name = holiday.name

    holiday.delete()

    log_activity(
        actor=request.user,
        action="config.holiday_deleted",
        action_label="Holiday deleted",
        module="CONFIG",
        target=holiday_name,
        severity="WARNING",
    )

    messages.success(request, f"Holiday '{holiday_name}' deleted.")

    return redirect("/configuration/?tab=holidays")


@login_required
def add_escalation_rule(request):

    if not _is_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        department_id = request.POST.get("department")
        department = get_object_or_404(Department, id=department_id, tenant=request.user.tenant)

        rule = EscalationRule.objects.create(
            tenant=request.user.tenant,
            department=department,
            priority=request.POST.get("priority"),
            escalate_after_hours=request.POST.get("escalate_after_hours") or 4,
            notify_email=request.POST.get("notify_email", ""),
            is_active="is_active" in request.POST,
        )

        log_activity(
            actor=request.user,
            action="config.escalation_rule_created",
            action_label="Escalation rule created",
            module="CONFIG",
            target=f"{department.name} - {rule.get_priority_display()}",
            severity="INFO",
        )

        messages.success(request, "Escalation rule created.")

    return redirect("/configuration/?tab=escalation")


@login_required
def edit_escalation_rule(request, rule_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    rule = get_object_or_404(EscalationRule, id=rule_id, tenant=request.user.tenant)

    if request.method == "POST":

        department_id = request.POST.get("department")
        rule.department = get_object_or_404(Department, id=department_id, tenant=request.user.tenant)
        rule.priority = request.POST.get("priority")
        rule.escalate_after_hours = request.POST.get("escalate_after_hours") or rule.escalate_after_hours
        rule.notify_email = request.POST.get("notify_email", "")
        rule.is_active = "is_active" in request.POST

        rule.save()

        log_activity(
            actor=request.user,
            action="config.escalation_rule_updated",
            action_label="Escalation rule updated",
            module="CONFIG",
            target=f"{rule.department.name} - {rule.get_priority_display()}",
            severity="INFO",
        )

        messages.success(request, "Escalation rule updated.")

    return redirect("/configuration/?tab=escalation")


@login_required
def delete_escalation_rule(request, rule_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    rule = get_object_or_404(EscalationRule, id=rule_id, tenant=request.user.tenant)
    rule_target = f"{rule.department.name} - {rule.get_priority_display()}"

    rule.delete()

    log_activity(
        actor=request.user,
        action="config.escalation_rule_deleted",
        action_label="Escalation rule deleted",
        module="CONFIG",
        target=rule_target,
        severity="WARNING",
    )

    messages.success(request, "Escalation rule deleted.")

    return redirect("/configuration/?tab=escalation")


@login_required
def add_email_template(request):

    if not _is_admin(request.user):
        return redirect('dashboard')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        template = EmailTemplate.objects.create(
            tenant=request.user.tenant,
            name=name,
            trigger_event=request.POST.get("trigger_event"),
            subject=request.POST.get("subject", ""),
            body=request.POST.get("body", ""),
            is_active="is_active" in request.POST,
        )

        log_activity(
            actor=request.user,
            action="config.email_template_created",
            action_label="Email template created",
            module="CONFIG",
            target=template.name,
            severity="INFO",
        )

        messages.success(request, f"Template '{name}' created.")

    return redirect("/configuration/?tab=templates")


@login_required
def edit_email_template(request, template_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    template = get_object_or_404(EmailTemplate, id=template_id, tenant=request.user.tenant)

    if request.method == "POST":

        template.name = request.POST.get("name", "").strip()
        template.trigger_event = request.POST.get("trigger_event")
        template.subject = request.POST.get("subject", "")
        template.body = request.POST.get("body", "")
        template.is_active = "is_active" in request.POST

        template.save()

        log_activity(
            actor=request.user,
            action="config.email_template_updated",
            action_label="Email template updated",
            module="CONFIG",
            target=template.name,
            severity="INFO",
        )

        messages.success(request, f"Template '{template.name}' updated.")

    return redirect("/configuration/?tab=templates")


@login_required
def delete_email_template(request, template_id):

    if not _is_admin(request.user):
        return redirect('dashboard')

    template = get_object_or_404(EmailTemplate, id=template_id, tenant=request.user.tenant)
    template_name = template.name

    template.delete()

    log_activity(
        actor=request.user,
        action="config.email_template_deleted",
        action_label="Email template deleted",
        module="CONFIG",
        target=template_name,
        severity="WARNING",
    )

    messages.success(request, f"Template '{template_name}' deleted.")

    return redirect("/configuration/?tab=templates")