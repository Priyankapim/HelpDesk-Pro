from django.core.management.base import BaseCommand
from departments.models import Department
from accounts.models import User


class Command(BaseCommand):
    help = "Backfills tenant on old departments that were created before multi-tenancy"

    def handle(self, *args, **options):

        broken = Department.objects.filter(tenant__isnull=True)

        if not broken.exists():
            self.stdout.write("No broken departments found.")
            return

        # Assign to the oldest/first tenant (where these departments were
        # actually being used before multi-tenant support existed)
        first_admin = User.objects.filter(
            role="ADMIN", tenant__isnull=False
        ).order_by("id").first()

        if not first_admin:
            self.stdout.write("No admin with a tenant found, aborting.")
            return

        count = broken.update(tenant=first_admin.tenant)

        self.stdout.write(
            self.style.SUCCESS(
                f"Fixed {count} department(s) -> tenant: {first_admin.tenant.name}"
            )
        )