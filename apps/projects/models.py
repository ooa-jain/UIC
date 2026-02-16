"""
Purpose: Project-related models
Contains:

Project (main project model)
ProjectApplication (student applications)
Milestone (project milestones)
Deliverable (student submissions)
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.accounts.models import Company, University, Student


class Project(models.Model):
    """Main project model"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending_review', 'Pending University Review'),
        ('rejected', 'Rejected'),
        ('open', 'Open for Applications'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    DOMAIN_CHOICES = (
        ('design', 'Design'),
        ('marketing', 'Marketing'),
        ('coding', 'Coding'),
        ('data_analysis', 'Data Analysis'),
        ('psychology', 'Psychology'),
        ('research', 'Research'),
        ('content_writing', 'Content Writing'),
        ('business_strategy', 'Business Strategy'),
        ('other', 'Other'),
    )

    TEAM_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('team', 'Team'),
    )

    POSTER_TYPE_CHOICES = (
        ('company', 'Company'),
        ('university', 'University'),
    )

    # NEW: Job Type Choices
    JOB_TYPE_CHOICES = (
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site'),
    )

    # Basic info - UPDATED to support both company and university posting
    poster_type = models.CharField(max_length=20, choices=POSTER_TYPE_CHOICES, default='company')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='projects')
    # For university-posted projects, they're both poster and reviewer
    posted_by_university = models.BooleanField(default=False)

    title = models.CharField(max_length=200)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES)
    description = models.TextField()

    # Requirements
    required_skills = models.TextField(help_text="Comma-separated skills")
    team_type = models.CharField(max_length=20, choices=TEAM_TYPE_CHOICES, default='individual')
    team_size = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    # NEW: Job Type Field
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='remote',
                                 help_text="Remote, Hybrid, or On-site")

    # Eligibility criteria
    eligible_departments = models.TextField(blank=True, help_text="Comma-separated departments, leave blank for all")
    min_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    eligible_years = models.CharField(max_length=100, blank=True, help_text="e.g., 2,3,4")

    # Payment - RENAMED FIELD (but keeping same DB column for backward compatibility)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                         verbose_name="Remuneration Amount")
    payment_type = models.CharField(max_length=20, choices=(
        ('fixed', 'Fixed Price'),
        ('milestone', 'Milestone-based'),
    ), default='fixed', verbose_name="Remuneration Type")

    # Timeline - RENAMED
    duration_weeks = models.IntegerField(help_text="Expected project duration in weeks")
    deadline = models.DateField(verbose_name="Project Closure Date")

    # Status and approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_reason = models.TextField(blank=True)

    # Attachments - RENAMED
    attachment = models.FileField(upload_to='project_attachments/', blank=True, null=True,
                                   verbose_name="Job Description (JD)",
                                   help_text="Upload the detailed job description document")

    # Assigned students
    assigned_students = models.ManyToManyField(Student, related_name='assigned_projects', blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_for_review_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']

    def __str__(self):
        poster_name = self.company.name if self.company else self.university.name
        return f"{self.title} - {poster_name}"

    def get_poster_name(self):
        """Get the name of whoever posted the project"""
        return self.company.name if self.company else self.university.name

    def get_poster_profile(self):
        """Get the profile object of whoever posted"""
        return self.company if self.company else self.university

    def is_poster_verified(self):
        """Check if poster is verified"""
        if self.company:
            return self.company.is_verified
        return self.university.is_verified

    def get_required_skills_list(self):
        return [skill.strip() for skill in self.required_skills.split(',') if skill.strip()]

    def get_eligible_departments_list(self):
        if not self.eligible_departments:
            return []
        return [dept.strip() for dept in self.eligible_departments.split(',') if dept.strip()]

    def get_eligible_years_list(self):
        if not self.eligible_years:
            return []
        return [year.strip() for year in self.eligible_years.split(',') if year.strip()]


class ProjectApplication(models.Model):
    """Student applications to projects"""
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='applications')

    # Application details
    cover_letter = models.TextField()
    proposed_approach = models.TextField(blank=True)
    portfolio_links = models.TextField(blank=True)

    # Team application
    is_team_application = models.BooleanField(default=False)
    team_members = models.ManyToManyField(Student, related_name='team_applications', blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'project_applications'
        unique_together = ['project', 'student']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.project.title}"

    def get_reviewer(self):
        """Returns who should review this application"""
        if self.project.posted_by_university:
            return self.project.university
        else:
            return self.project.company

class Milestone(models.Model):
    """Project milestones for tracking progress"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('revision_required', 'Revision Required'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')

    title = models.CharField(max_length=200)
    description = models.TextField()
    order = models.IntegerField(default=1)

    # Payment (for milestone-based projects)
    payment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Dates
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'milestones'
        ordering = ['project', 'order']

    def __str__(self):
        return f"{self.project.title} - {self.title}"


class Deliverable(models.Model):
    """Student submissions and deliverables"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='deliverables')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='deliverables')
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='deliverables')

    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='deliverables/')
    submission_notes = models.TextField(blank=True)

    # Review
    is_approved = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)
    revision_required = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'deliverables'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.title} - {self.project.title}"