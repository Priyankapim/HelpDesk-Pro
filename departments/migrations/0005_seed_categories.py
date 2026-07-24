from django.db import migrations


DEPARTMENT_CATEGORY_MAP = {
    "IT Support": [
        "Hardware Issue", "Software Issue", "Network Issue", "Email / Outlook",
    ],
    "HR Support": [
        "New Employee Onboarding", "Leave Policy", "Payroll Inquiry",
    ],
    "Admin Support": [
        "Office Supplies", "Facility Request",
    ],
    "Finance Requests": [
        "Invoice Processing", "Budget Approval",
    ],
    "Asset Requests": [
        "Laptop Request", "Software License",
    ],
    "Access Management": [
        "Account Creation", "Permission Request", "VPN Access",
    ],
    "General Services": [
        "General Inquiry",
    ],
}


def seed_categories(apps, schema_editor):

    Department = apps.get_model('departments', 'Department')
    Category = apps.get_model('departments', 'Category')

    for department_name, category_names in DEPARTMENT_CATEGORY_MAP.items():

        department = Department.objects.filter(name=department_name).first()

        if not department:
            continue

        for category_name in category_names:

            Category.objects.get_or_create(
                department=department,
                name=category_name,
            )


def reverse_seed_categories(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('departments', '0004_category'),
    ]

    operations = [
        migrations.RunPython(seed_categories, reverse_seed_categories),
    ]