from .models import AuditLog


def log_activity(actor, action, action_label, module, target,
                  severity='INFO', before=None, after=None):
    """
    Central helper used across the project to write an Audit Log entry.

    actor        : request.user (or None for system generated actions)
    action       : machine readable slug, e.g. "user.role_updated"
    action_label : human readable label, e.g. "User role updated"
    module       : one of AuditLog.MODULE_CHOICES
    target       : human readable target, e.g. user's email / department name
    severity     : INFO / WARNING / CRITICAL
    before       : dict of old values (optional)
    after        : dict of new values (optional)
    """

    return AuditLog.objects.create(
        actor=actor if (actor is not None and getattr(actor, "is_authenticated", False)) else None,
        action=action,
        action_label=action_label,
        module=module,
        target=target,
        severity=severity,
        changes_before=before,
        changes_after=after,
    )
