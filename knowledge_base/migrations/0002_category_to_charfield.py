from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_base', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='category',
        ),
        migrations.DeleteModel(
            name='Category',
        ),
        migrations.AddField(
            model_name='article',
            name='category',
            field=models.CharField(
                blank=True,
                max_length=100,
                choices=[
                    ('Hardware Issue', 'Hardware Issue'),
                    ('Software Issue', 'Software Issue'),
                    ('Network Issue', 'Network Issue'),
                    ('Email / Outlook', 'Email / Outlook'),
                    ('New Employee Onboarding', 'New Employee Onboarding'),
                    ('Leave Policy', 'Leave Policy'),
                    ('Payroll Inquiry', 'Payroll Inquiry'),
                    ('Office Supplies', 'Office Supplies'),
                    ('Facility Request', 'Facility Request'),
                    ('Invoice Processing', 'Invoice Processing'),
                    ('Budget Approval', 'Budget Approval'),
                    ('Laptop Request', 'Laptop Request'),
                    ('Software License', 'Software License'),
                    ('Account Creation', 'Account Creation'),
                    ('Permission Request', 'Permission Request'),
                    ('VPN Access', 'VPN Access'),
                    ('General Inquiry', 'General Inquiry'),
                ],
            ),
        ),
    ]