"""
Purpose: Defines User, Student, Company, University models
Contains:

User (custom user model)
Student (student profile)
Company (company profile)
University (university admin profile)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

#has a one to one connection to each type of user. when any type of user is created like uni etc then the User is also created cause uni is a type of user

class User(AbstractUser):
    """Extended user model with role-based access"""
    USER_TYPES = (
        ('student', 'Student'),
        ('company', 'Company'),
        ('university', 'University Admin'),
    )

    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class University(models.Model):
    """University profile and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='university_profile')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='universities/', blank=True, null=True)
    address = models.TextField()
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)

    # Admin details
    admin_name = models.CharField(max_length=100)
    admin_email = models.EmailField()
    admin_phone = models.CharField(max_length=15)

    # Settings
    is_verified = models.BooleanField(default=False)
    auto_approve_projects = models.BooleanField(default=False)
    min_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'universities'
        verbose_name_plural = 'Universities'

    def __str__(self):
        return self.name


# apps/accounts/models.py - UPDATE Company model

class Company(models.Model):
    """Company profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='companies/', blank=True, null=True)
    industry = models.CharField(max_length=100)
    website = models.URLField(blank=True)
    description = models.TextField()

    # Contact details - UPDATED
    contact_person = models.CharField(max_length=100, help_text="SPOC (Single Point of Contact)")
    contact_email = models.EmailField(help_text="Official company email")
    contact_phone = models.CharField(max_length=15)
    address = models.TextField()

    # NEW: Official company details for verification
    company_registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Company Registration/CIN Number"
    )
    gst_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="GST Number (optional)"
    )

    # Verification - UPDATED
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending Verification'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )
    verified_by = models.ForeignKey(
        'University',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_companies'
    )
    verification_document = models.FileField(
        upload_to='company_docs/',
        blank=True,
        null=True,
        help_text="Upload company registration certificate, GST certificate, or incorporation documents"
    )
    rejection_reason = models.TextField(blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Stats
    total_projects_posted = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0,
                                 validators=[MinValueValidator(0), MaxValueValidator(5)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return self.name
# apps/accounts/models.py - UPDATE the Student model

class Student(models.Model):
    """Student profile"""
    YEAR_CHOICES = (
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
        ('graduate', 'Graduate'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')

    # UPDATED: Make university nullable so students can register first, then select university
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='students',
        null=True,  # ← ADD THIS
        blank=True  # ← ADD THIS
    )

    # Academic details
    student_id = models.CharField(max_length=50, blank=True)  # ← Also make blank=True
    department = models.CharField(max_length=100)
    year = models.CharField(max_length=20, choices=YEAR_CHOICES)
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                              validators=[MinValueValidator(0), MaxValueValidator(10)])

    # Profile
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='students/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    portfolio_url = models.URLField(blank=True)

    # Skills
    skills = models.TextField(help_text="Comma-separated skills", blank=True)  # ← Make blank=True

    # Stats
    projects_completed = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0,
                                 validators=[MinValueValidator(0), MaxValueValidator(5)])
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Preferences
    available_for_projects = models.BooleanField(default=True)
    preferred_domains = models.TextField(blank=True, help_text="Comma-separated domains")

    # NEW: Verification fields
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending Verification'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ),
        default='pending'
    )
    university_email = models.EmailField(blank=True, help_text="Your university email address")
    rejection_reason = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        University,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_students'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.student_id if self.student_id else 'No ID'}"

    def get_skills_list(self):
        """Return skills as a list"""
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]

    def get_preferred_domains_list(self):
        """Return preferred domains as a list"""
        return [domain.strip() for domain in self.preferred_domains.split(',') if domain.strip()for domain in self.preferred_domains.split(',') if domain.strip()]