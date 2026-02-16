# Create this file: apps/projects/migrations/0003_add_job_type.py
# Run after creating: python manage.py makemigrations
# Then: python manage.py migrate

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),  # Adjust this to your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='job_type',
            field=models.CharField(
                choices=[
                    ('remote', 'Remote'),
                    ('hybrid', 'Hybrid'),
                    ('onsite', 'On-site')
                ],
                default='remote',
                help_text='Remote, Hybrid, or On-site',
                max_length=20
            ),
        ),
    ]