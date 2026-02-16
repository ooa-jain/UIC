# Save this as: apps/projects/management/commands/create_test_data.py
# Create the folders: apps/projects/management/commands/

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Company, University, Student
from apps.projects.models import Project
from datetime import date, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test data for the platform'

    def handle(self, *args, **kwargs):
        # Create University
        uni_user, created = User.objects.get_or_create(
            username='university_admin',
            defaults={
                'email': 'university@example.com',
                'user_type': 'university',
                'is_active': True
            }
        )
        if created:
            uni_user.set_password('password123')
            uni_user.save()
            self.stdout.write(self.style.SUCCESS('University user created'))

        university, created = University.objects.get_or_create(
            user=uni_user,
            defaults={
                'name': 'Tech University',
                'address': '123 University Lane, Tech City',
                'contact_email': 'contact@techuni.edu',
                'contact_phone': '1234567890'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'University created: {university.name}'))

        # Create Company
        company_user, created = User.objects.get_or_create(
            username='techcorp',
            defaults={
                'email': 'hr@techcorp.com',
                'user_type': 'company',
                'is_active': True
            }
        )
        if created:
            company_user.set_password('password123')
            company_user.save()
            self.stdout.write(self.style.SUCCESS('Company user created'))

        company, created = Company.objects.get_or_create(
            user=company_user,
            defaults={
                'name': 'TechCorp Solutions',
                'industry': 'Information Technology',
                'description': 'Leading software development company',
                'website': 'https://techcorp.com',
                'is_verified': True,
                'rating': 4.5
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Company created: {company.name}'))

        # Create Student
        student_user, created = User.objects.get_or_create(
            username='john_doe',
            defaults={
                'email': 'john@student.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'user_type': 'student',
                'is_active': True
            }
        )
        if created:
            student_user.set_password('password123')
            student_user.save()
            self.stdout.write(self.style.SUCCESS('Student user created'))

        student, created = Student.objects.get_or_create(
            user=student_user,
            defaults={
                'university': university,
                'department': 'Computer Science',
                'year': 3,
                'gpa': 3.8,
                'enrollment_number': 'CS2022001'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Student created: {student.user.get_full_name()}'))

        # Create Sample Projects
        projects_data = [
            {
                'title': 'E-commerce Website Development',
                'domain': 'coding',
                'description': 'Build a full-stack e-commerce platform with payment integration',
                'required_skills': 'React, Node.js, MongoDB, Payment Gateway',
                'payment_amount': 75000,
                'duration_weeks': 12,
                'team_type': 'team',
                'team_size': 3
            },
            {
                'title': 'Mobile App UI/UX Design',
                'domain': 'design',
                'description': 'Design modern and intuitive mobile app interface',
                'required_skills': 'Figma, Adobe XD, UI/UX Principles',
                'payment_amount': 30000,
                'duration_weeks': 6,
                'team_type': 'individual',
                'team_size': 1
            },
            {
                'title': 'Social Media Marketing Campaign',
                'domain': 'marketing',
                'description': 'Create and execute a comprehensive social media strategy',
                'required_skills': 'Social Media Marketing, Content Creation, Analytics',
                'payment_amount': 25000,
                'duration_weeks': 8,
                'team_type': 'team',
                'team_size': 2
            },
            {
                'title': 'Data Analysis for Sales Optimization',
                'domain': 'data_analysis',
                'description': 'Analyze sales data and provide actionable insights',
                'required_skills': 'Python, Pandas, Data Visualization, Statistics',
                'payment_amount': 40000,
                'duration_weeks': 10,
                'team_type': 'individual',
                'team_size': 1
            }
        ]

        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                title=project_data['title'],
                company=company,
                defaults={
                    **project_data,
                    'university': university,
                    'payment_type': 'fixed',
                    'deadline': date.today() + timedelta(days=90),
                    'status': 'open',
                    'eligible_departments': 'Computer Science, IT, Design',
                    'min_gpa': 3.0,
                    'eligible_years': '2,3,4'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Project created: {project.title}'))

        self.stdout.write(self.style.SUCCESS('\n=== Test Data Created Successfully ==='))
        self.stdout.write(self.style.SUCCESS('\nLogin Credentials:'))
        self.stdout.write(self.style.WARNING('University: university_admin / password123'))
        self.stdout.write(self.style.WARNING('Company: techcorp / password123'))
        self.stdout.write(self.style.WARNING('Student: john_doe / password123'))