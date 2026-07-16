from django.contrib.auth import get_user_model

from .models import AutomationRule


def _get_field_value(ticket, field):
    """
    Reads the current value of a ticket field used in a rule condition.
    """

    if field == "priority":
        return ticket.priority or ""

    if field == "status":
        return ticket.status or ""

    if field == "department_id":
        return str(ticket.department_id or "")

    if field == "assignee":
        if ticket.assigned_to:
            return ticket.assigned_to.email
        return ""

    return ""


def _condition_matches(condition, ticket):
    """
    Evaluates a single RuleCondition against the ticket.
    """

    actual = _get_field_value(ticket, condition.field).strip().lower()
    expected = (condition.value or "").strip().lower()

    if condition.operator == "equals":
        return actual == expected

    if condition.operator == "not_equals":
        return actual != expected

    if condition.operator == "contains":
        return expected in actual

    if condition.operator == "not_contains":
        return expected not in actual

    if condition.operator == "is_empty":
        return actual == ""

    if condition.operator == "is_not_empty":
        return actual != ""

    return False


def _rule_matches(rule, ticket):
    """
    AND logic - every condition on the rule must pass.
    A rule with no conditions always fires on its trigger.
    """

    for condition in rule.conditions.all():
        if not _condition_matches(condition, ticket):
            return False

    return True


def _get_recipient(ticket):
    """
    Default recipient for notification/email actions:
    the assigned agent if the ticket has one, otherwise the
    person who raised the ticket.
    """

    if ticket.assigned_to:
        return ticket.assigned_to

    return ticket.created_by


def _run_action(action, ticket):
    """
    Executes a single RuleAction against the ticket.
    """

    from tickets.models import Notification
    from notifications.utils import send_ticket_email

    User = get_user_model()

    if action.action_type == "assign_agent":

        if action.value:

            agent = User.objects.filter(
                email__iexact=action.value.strip()
            ).first()

            if not agent:
                agent = User.objects.filter(
                    username__iexact=action.value.strip()
                ).first()

            if agent:
                ticket.assigned_to = agent
                ticket.save(update_fields=["assigned_to"])

    elif action.action_type == "change_priority":

        if action.value:
            ticket.priority = action.value.strip()
            ticket.save(update_fields=["priority"])

    elif action.action_type == "change_status":

        if action.value:
            ticket.status = action.value.strip()
            ticket.save(update_fields=["status"])

    elif action.action_type == "add_tag":

        if action.value:

            existing_tags = [
                t.strip() for t in (ticket.tags or "").split(",") if t.strip()
            ]

            new_tag = action.value.strip()

            if new_tag not in existing_tags:
                existing_tags.append(new_tag)
                ticket.tags = ", ".join(existing_tags)
                ticket.save(update_fields=["tags"])

    elif action.action_type == "send_notification":

        recipient = _get_recipient(ticket)

        if recipient:

            Notification.objects.create(
                user=recipient,
                ticket=ticket,
                title="Automation Rule Triggered",
                message=action.value or f"Rule fired for ticket {ticket.ticket_number}."
            )

    elif action.action_type == "send_email_notification":

        recipient = _get_recipient(ticket)

        if recipient and recipient.email:

            try:
                send_ticket_email(
                    subject="ServiceDesk Pro - Automation Notification",
                    message=(
                        action.value
                        or f"Automation rule triggered for ticket {ticket.ticket_number}."
                    ),
                    recipient=recipient.email
                )
            except Exception:
                # Don't let a broken email config break the whole automation run
                pass


def run_automation_rules(trigger, ticket, extra=None):
    """
    Entry point called from ticket views whenever a trigger event happens.

    trigger: one of AutomationRule.TRIGGER_CHOICES values, e.g. "TICKET_CREATED"
    ticket: the Ticket instance the event happened on
    extra: optional dict with extra context (not required by any action yet,
           kept for future triggers like old_status/new_status)
    """

    rules = AutomationRule.objects.filter(
        trigger=trigger,
        is_active=True
    ).prefetch_related("conditions", "actions")

    for rule in rules:

        if not _rule_matches(rule, ticket):
            continue

        for action in rule.actions.all():
            _run_action(action, ticket)

        rule.execution_count = rule.execution_count + 1
        rule.save(update_fields=["execution_count"])
