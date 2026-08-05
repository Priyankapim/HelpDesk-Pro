from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import User
from departments.models import Department
from automation.models import AutomationRule
from configuration.models import WorkingHours, Holiday, EscalationRule, EmailTemplate
from knowledge_base.models import Article


class Command(BaseCommand):
    help = "Backfills tenant on all models that were made tenant-aware after launch"

    def handle(self, *args, **options):

        first_admin = User.objects.filter(
            role="ADMIN", tenant__isnull=False
        ).order_by("id").first()

        if not first_admin:
            self.stdout.write("No admin with a tenant found, aborting.")
            return

        tenant = first_admin.tenant

        with transaction.atomic():

            dept_count = Department.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Departments fixed: {dept_count}")

            rule_count = AutomationRule.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Automation rules fixed: {rule_count}")

            wh_count = WorkingHours.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Working hours rows fixed: {wh_count}")

            holiday_count = Holiday.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Holidays fixed: {holiday_count}")

            esc_count = EscalationRule.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Escalation rules fixed: {esc_count}")

            tmpl_count = EmailTemplate.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Email templates fixed: {tmpl_count}")

            article_count = Article.objects.filter(tenant__isnull=True).update(tenant=tenant)
            self.stdout.write(f"Knowledge base articles fixed: {article_count}")

        self.stdout.write(
            self.style.SUCCESS(f"Done. Everything assigned to tenant: {tenant.name}")
        )