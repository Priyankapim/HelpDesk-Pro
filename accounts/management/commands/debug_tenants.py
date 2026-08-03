from django.core.management.base import BaseCommand
from accounts.models import User
from tickets.models import Ticket


class Command(BaseCommand):
    help = "Prints tenant info for all users and tickets"

    def handle(self, *args, **options):

        self.stdout.write("---- USERS ----")
        for user in User.objects.all().order_by("id"):
            self.stdout.write(
                f"id={user.id} email={user.email} role={user.role} "
                f"tenant_id={user.tenant_id} tenant_name={user.tenant.name if user.tenant_id else None}"
            )

        self.stdout.write("---- TICKETS ----")
        for ticket in Ticket.objects.all().order_by("id"):
            self.stdout.write(
                f"id={ticket.id} number={ticket.ticket_number} "
                f"created_by={ticket.created_by.email if ticket.created_by_id else None} "
                f"tenant_id={ticket.tenant_id}"
            )