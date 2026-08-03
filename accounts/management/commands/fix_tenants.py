from django.core.management.base import BaseCommand
from accounts.models import User
from tickets.models import Ticket


class Command(BaseCommand):
    help = "Backfills tenant_id on Users/Tickets that were created without one (old bug)"

    def handle(self, *args, **options):

        broken_users = User.objects.filter(
            tenant__isnull=True,
            role__in=["ADMIN", "AGENT", "EMPLOYEE"]
        )

        fixed_count = 0

        for user in broken_users:

            tenant = None

            if user.department_id and user.department.tenant_id:
                tenant = user.department.tenant

            if not tenant and user.role in ["AGENT", "EMPLOYEE"]:
                admin = User.objects.filter(
                    role="ADMIN",
                    tenant__isnull=False
                ).first()
                if admin:
                    tenant = admin.tenant

            if tenant:
                user.tenant = tenant
                user.save(update_fields=["tenant"])
                fixed_count += 1
                self.stdout.write(f"Fixed user: {user.email} -> {tenant.name}")

        broken_tickets = Ticket.objects.filter(tenant__isnull=True)
        ticket_fixed = 0

        for ticket in broken_tickets:
            if ticket.created_by_id and ticket.created_by.tenant_id:
                ticket.tenant = ticket.created_by.tenant
                ticket.save(update_fields=["tenant"])
                ticket_fixed += 1
                self.stdout.write(f"Fixed ticket: {ticket.ticket_number}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Users fixed: {fixed_count}. Tickets fixed: {ticket_fixed}."
            )
        )