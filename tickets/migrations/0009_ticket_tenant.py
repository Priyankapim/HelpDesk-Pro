from django.db import migrations, models
import django.db.models.deletion


def backfill_tenant(apps, schema_editor):
    Ticket = apps.get_model('tickets', 'Ticket')
    for ticket in Ticket.objects.select_related('created_by').all():
        if ticket.created_by_id and ticket.created_by.tenant_id:
            ticket.tenant_id = ticket.created_by.tenant_id
            ticket.save(update_fields=['tenant'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
        ('tickets', '0008_alter_ticket_category_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='tenant',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tickets',
                to='tenants.tenant',
            ),
        ),
        migrations.RunPython(backfill_tenant, noop_reverse),
    ]