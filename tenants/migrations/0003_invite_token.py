import uuid

from django.db import migrations, models


def populate_tokens(apps, schema_editor):
    Invite = apps.get_model('tenants', 'Invite')
    for invite in Invite.objects.all():
        invite.token = uuid.uuid4()
        invite.save(update_fields=['token'])


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0002_invite'),
    ]

    operations = [
        migrations.AddField(
            model_name='invite',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(populate_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='invite',
            name='token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]