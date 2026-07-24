from django.db import migrations, models


OLD_CATEGORIES = [
    "Hardware Issue",
    "Software Issue",
    "Network Issue",
    "Email / Outlook",
    "New Employee Onboarding",
    "Leave Policy",
    "Payroll Inquiry",
    "Office Supplies",
    "Facility Request",
    "Invoice Processing",
    "Budget Approval",
    "Laptop Request",
    "Software License",
    "Account Creation",
    "Permission Request",
    "VPN Access",
    "General Inquiry",
]


def seed_categories(apps, schema_editor):
    Category = apps.get_model('tickets', 'Category')

    for name in OLD_CATEGORIES:
        Category.objects.get_or_create(name=name)


def remove_seeded_categories(apps, schema_editor):
    Category = apps.get_model('tickets', 'Category')
    Category.objects.filter(name__in=OLD_CATEGORIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0006_alter_ticket_affected_system'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.RunPython(seed_categories, remove_seeded_categories),
    ]
