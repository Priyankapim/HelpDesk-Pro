# Ensures a known-working superuser exists so /admin/ is always reachable,
# even without shell access (e.g. Render free tier).
#
# Runs automatically on every deploy via Procfile's "release: python manage.py migrate".
#
# Login with:
#   email:    superadmin@helpdesk.local
#   password: HelpDesk@2026
#
# IMPORTANT: change this password from the admin panel once you're in,
# then feel free to delete this migration file (it's idempotent either way —
# safe to leave in, it just won't do anything once removed/edited).

from django.db import migrations


def ensure_superuser(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    email = "superadmin@helpdesk.local"

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": "superadmin",
            "role": "SUPER_ADMIN",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )

    # Force these regardless of whether the row already existed,
    # in case it was previously created without staff/superuser rights.
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.role = "SUPER_ADMIN"

    # Set a known password every time this migration runs so login
    # always works, even if it was changed to something unknown before.
    from django.contrib.auth.hashers import make_password
    user.password = make_password("HelpDesk@2026")

    user.save()


def reverse_noop(apps, schema_editor):
    # Intentionally left blank — we don't want `migrate` backwards to delete the account.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_merge_20260722_1200'),
    ]

    operations = [
        migrations.RunPython(ensure_superuser, reverse_noop),
    ]