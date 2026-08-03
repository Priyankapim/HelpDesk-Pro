from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from .models import AutomationRule, RuleCondition, RuleAction


def _save_conditions_and_actions(request, rule):
    """
    Wipes and re-creates the conditions/actions for a rule based on the
    posted arrays. Shared by add_automation_rule and edit_automation_rule.
    """

    rule.conditions.all().delete()
    rule.actions.all().delete()

    cond_fields = request.POST.getlist("cond_field[]")
    cond_operators = request.POST.getlist("cond_operator[]")
    cond_values = request.POST.getlist("cond_value[]")

    for field, operator, value in zip(cond_fields, cond_operators, cond_values):

        if field and operator:

            RuleCondition.objects.create(
                rule=rule,
                field=field,
                operator=operator,
                value=value.strip()
            )

    action_types = request.POST.getlist("action_type[]")
    action_values = request.POST.getlist("action_value[]")

    for action_type, value in zip(action_types, action_values):

        if action_type:

            RuleAction.objects.create(
                rule=rule,
                action_type=action_type,
                value=value.strip()
            )


@login_required
def automation_list(request):

    if request.user.role != 'ADMIN':
        return redirect('dashboard')

    rules = AutomationRule.objects.all().prefetch_related(
        'conditions', 'actions'
    ).order_by('-created_at')

    selected_trigger = request.GET.get('trigger')

    if selected_trigger:
        rules = rules.filter(trigger=selected_trigger)

    total_rules = AutomationRule.objects.count()

    active_rules = AutomationRule.objects.filter(
        is_active=True
    ).count()

    total_executions = AutomationRule.objects.aggregate(
        total=Sum('execution_count')
    )['total'] or 0

    # Data used by JS to populate the Edit modal without reloading the page

    rules_json = {}

    for rule in rules:

        rules_json[rule.id] = {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "trigger": rule.trigger,
            "is_active": rule.is_active,
            "conditions": [
                {
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value
                }
                for c in rule.conditions.all()
            ],
            "actions": [
                {
                    "action_type": a.action_type,
                    "value": a.value
                }
                for a in rule.actions.all()
            ],
        }

    context = {

        "rules": rules,

        "total_rules": total_rules,

        "active_rules": active_rules,

        "total_executions": total_executions,

        "trigger_choices": AutomationRule.TRIGGER_CHOICES,

        "trigger_descriptions": AutomationRule.TRIGGER_DESCRIPTIONS,

        "selected_trigger": selected_trigger,

        "field_choices": RuleCondition.FIELD_CHOICES,

        "operator_choices": RuleCondition.OPERATOR_CHOICES,

        "action_choices": RuleAction.ACTION_CHOICES,

        "rules_json": rules_json,

    }

    return render(
        request,
        "automation_list.html",
        context
    )


@login_required
def add_automation_rule(request):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        trigger = request.POST.get("trigger", "").strip()

        if not name or not trigger:
            messages.error(request, "Rule name and trigger are required.")
            return redirect("automation_list")

        rule = AutomationRule.objects.create(
            name=name,
            description=request.POST.get("description", "").strip(),
            trigger=trigger,
            is_active=bool(request.POST.get("is_active")),
            created_by=request.user
        )

        _save_conditions_and_actions(request, rule)

        messages.success(request, f"Automation rule '{name}' created.")

        return redirect("automation_list")

    return redirect("automation_list")


@login_required
def edit_automation_rule(request, rule_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    rule = get_object_or_404(AutomationRule, id=rule_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        trigger = request.POST.get("trigger", "").strip()

        if not name or not trigger:
            messages.error(request, "Rule name and trigger are required.")
            return redirect("automation_list")

        rule.name = name
        rule.description = request.POST.get("description", "").strip()
        rule.trigger = trigger
        rule.is_active = bool(request.POST.get("is_active"))
        rule.save()

        _save_conditions_and_actions(request, rule)

        messages.success(request, f"Automation rule '{name}' updated.")

        return redirect("automation_list")

    return redirect("automation_list")


@login_required
def toggle_automation_rule(request, rule_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    rule = get_object_or_404(AutomationRule, id=rule_id)

    rule.is_active = not rule.is_active
    rule.save()

    if rule.is_active:
        messages.success(request, f"'{rule.name}' is now active.")
    else:
        messages.success(request, f"'{rule.name}' is now inactive.")

    return redirect("automation_list")


@login_required
def delete_automation_rule(request, rule_id):

    if request.user.role not in ['ADMIN', 'SUPER_ADMIN']:
        return redirect('dashboard')

    rule = get_object_or_404(AutomationRule, id=rule_id)
    rule.delete()

    messages.success(request, "Automation rule deleted.")

    return redirect("automation_list")