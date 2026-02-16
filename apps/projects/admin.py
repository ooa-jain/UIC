"""Purpose: Django admin panel configuration
Registers: Project, ProjectApplication, Milestone, Deliverable"""


from django.contrib import admin
from .models import Project, ProjectApplication, Milestone, Deliverable


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'university', 'domain', 'status',
                    'payment_amount', 'deadline', 'created_at']
    list_filter = ['status', 'domain', 'team_type', 'payment_type', 'created_at']
    search_fields = ['title', 'description', 'company__name']
    date_hierarchy = 'created_at'

    # Use autocomplete_fields instead of raw_id_fields
    autocomplete_fields = ['company', 'university']
    filter_horizontal = ['assigned_students']

    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'university', 'title', 'domain', 'description')
        }),
        ('Project Requirements', {
            'fields': ('required_skills', 'team_type', 'team_size')
        }),
        ('Eligibility Criteria', {
            'fields': ('eligible_departments', 'min_gpa', 'eligible_years'),
            'classes': ('collapse',)
        }),
        ('Payment & Timeline', {
            'fields': ('payment_amount', 'payment_type', 'duration_weeks', 'deadline')
        }),
        ('Project Status', {
            'fields': ('status', 'rejection_reason', 'assigned_students')
        }),
        ('Attachments', {
            'fields': ('attachment',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectApplication)
class ProjectApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'project', 'status', 'is_team_application', 'created_at']
    list_filter = ['status', 'is_team_application', 'created_at']
    search_fields = ['student__user__username', 'student__user__first_name',
                     'student__user__last_name', 'project__title']
    autocomplete_fields = ['project', 'student']
    filter_horizontal = ['team_members']
    date_hierarchy = 'created_at'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'order', 'payment_percentage', 'due_date', 'status']
    list_filter = ['status', 'due_date']
    search_fields = ['title', 'project__title']
    autocomplete_fields = ['project']


@admin.register(Deliverable)
class DeliverableAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'student', 'is_approved',
                    'revision_required', 'submitted_at']
    list_filter = ['is_approved', 'revision_required', 'submitted_at']
    search_fields = ['title', 'project__title', 'student__user__username']
    autocomplete_fields = ['project', 'student']
    date_hierarchy = 'submitted_at'




