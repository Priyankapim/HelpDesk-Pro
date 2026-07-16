from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('slug', models.SlugField(blank=True, max_length=180, unique=True)),
                ('plan', models.CharField(choices=[('TRIAL', 'Trial'), ('STARTER', 'Starter'), ('PROFESSIONAL', 'Professional'), ('ENTERPRISE', 'Enterprise')], default='TRIAL', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('max_users', models.PositiveIntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('trial_ends_at', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
