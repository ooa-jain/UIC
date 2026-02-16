"""
Purpose: All project-related views
Contains:

ProjectListView
ProjectDetailView
ProjectCreateView
ProjectApplyView
ManageApplicationsView
PendingReviewView
ProjectWorkspaceView
And many more...
"""
from django.db.models import Q
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from .models import Project, ProjectApplication, Deliverable, Milestone
from .forms import ProjectForm, ProjectApplicationForm, DeliverableForm, MilestoneForm
from apps.accounts.models import Company, University, Student
from django.db import models

from ..accounts.views import UniversityRequiredMixin



class ProjectListView(ListView):
    """List all available projects - filtered by student's university"""
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        # Base queryset - only open projects
        queryset = Project.objects.filter(status='open')

        # IMPORTANT: Filter by student's university if user is a student
        user = self.request.user
        if user.is_authenticated and user.user_type == 'student' and hasattr(user, 'student_profile'):
            student_university = user.student_profile.university

            # UPDATED: Handle case where student hasn't selected university yet
            if student_university:
                # Only show projects posted TO or BY their university
                queryset = queryset.filter(university=student_university)
            else:
                # If no university selected, show no projects
                queryset = Project.objects.none()

        # Filter by domain
        domain = self.request.GET.get('domain')
        if domain:
            queryset = queryset.filter(domain=domain)

        # Filter by university (for non-students or additional filtering)
        university_id = self.request.GET.get('university')
        if university_id:
            queryset = queryset.filter(university_id=university_id)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(required_skills__icontains=search)
            )

        # Filter by payment range
        min_payment = self.request.GET.get('min_payment')
        max_payment = self.request.GET.get('max_payment')
        if min_payment:
            queryset = queryset.filter(payment_amount__gte=min_payment)
        if max_payment:
            queryset = queryset.filter(payment_amount__lte=max_payment)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # For students, show only their university
        user = self.request.user
        if user.is_authenticated and user.user_type == 'student' and hasattr(user, 'student_profile'):
            student_university = user.student_profile.university
            if student_university:
                context['universities'] = University.objects.filter(
                    id=student_university.id,
                    is_verified=True
                )
                context['student_university'] = student_university
            else:
                context['universities'] = University.objects.none()
                context['student_university'] = None
        else:
            context['universities'] = University.objects.filter(is_verified=True)

        context['domain_choices'] = Project.DOMAIN_CHOICES
        return context
class ProjectDetailView(DetailView):
    """View project details"""
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'

    def get_queryset(self):
        """Restrict which projects user can view"""
        user = self.request.user

        if not user.is_authenticated:
            # Anonymous users can only see open projects
            return Project.objects.filter(status='open')

        # Students can see open projects + projects they applied to
        if user.user_type == 'student' and hasattr(user, 'student_profile'):
            return Project.objects.filter(
                Q(status='open') |  # Open projects
                Q(assigned_students=user.student_profile) |  # Assigned projects
                Q(applications__student=user.student_profile)  # Applied projects
            ).distinct()

        # Companies can see only their own projects
        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return Project.objects.filter(company=user.company_profile)

        # Universities can see projects submitted to them
        if user.user_type == 'university' and hasattr(user, 'university_profile'):
            return Project.objects.filter(university=user.university_profile)

        # Default: only open projects
        return Project.objects.filter(status='open')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user

        if user.is_authenticated:
            if user.user_type == 'student' and hasattr(user, 'student_profile'):
                context['has_applied'] = ProjectApplication.objects.filter(
                    project=project,
                    student=user.student_profile
                ).exists()

            if user.user_type == 'company' and hasattr(user, 'company_profile'):
                # FIX: Check if project.company exists before accessing .user
                if project.company and project.company.user == user:
                    context['applications'] = project.applications.all()
                    context['can_manage'] = True

            if user.user_type == 'university' and hasattr(user, 'university_profile'):
                if project.university.user == user:
                    context['can_review'] = True
                    # NEW: Add can_manage for university-posted projects
                    context['can_manage'] = project.posted_by_university

        context['milestones'] = project.milestones.all()
        return context


class ProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create new project (Company or University)"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/create.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        # Allow both companies and universities to post
        if self.request.user.user_type == 'company':
            profile = getattr(self.request.user, 'company_profile', None)
            # UPDATED: Companies must be verified to post
            if not profile or not profile.is_verified:
                messages.error(
                    self.request,
                    '⚠️ Your company must be verified by a university before you can post projects.'
                )
                return False
            return True
        elif self.request.user.user_type == 'university':
            return hasattr(self.request.user, 'university_profile')
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['universities'] = University.objects.filter(is_verified=True)
        context['is_university_posting'] = self.request.user.user_type == 'university'
        return context

    def form_valid(self, form):
        user = self.request.user

        if user.user_type == 'company':
            # Company posting
            form.instance.company = user.company_profile
            form.instance.poster_type = 'company'
            form.instance.posted_by_university = False
            form.instance.status = 'pending_review'
            form.instance.submitted_for_review_at = timezone.now()

            # Increment company's project count
            company = user.company_profile
            company.total_projects_posted += 1
            company.save()

            messages.success(self.request, 'Project submitted for university review!')

        elif user.user_type == 'university':
            # University posting - auto-approved
            form.instance.university = user.university_profile
            form.instance.poster_type = 'university'
            form.instance.posted_by_university = True
            form.instance.company = None
            form.instance.status = 'open'  # Auto-approved
            form.instance.approved_at = timezone.now()

            messages.success(self.request, 'Project posted successfully and is now open for applications!')

        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # If the logged-in user is a university, university field should not be required
        if self.request.user.user_type == 'university':
            form.fields['university'].required = False

        return form


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit project (Company only, before approval)"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/edit.html'

    def test_func(self):
        project = self.get_object()
        return (self.request.user.user_type == 'company' and
                hasattr(self.request.user, 'company_profile') and
                project.company.user == self.request.user and
                project.status in ['draft', 'rejected'])

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Project updated successfully!')
        return super().form_valid(form)


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete project (Company only)"""
    model = Project
    template_name = 'projects/delete.html'
    success_url = reverse_lazy('projects:list')

    def test_func(self):
        project = self.get_object()
        return (self.request.user.user_type == 'company' and
                hasattr(self.request.user, 'company_profile') and
                project.company.user == self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Project deleted successfully!')
        return super().delete(request, *args, **kwargs)


class ProjectApplyView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Apply to project (Student only)"""
    model = ProjectApplication
    form_class = ProjectApplicationForm
    template_name = 'projects/apply.html'

    def test_func(self):
        if self.request.user.user_type != 'student':
            return False
        if not hasattr(self.request.user, 'student_profile'):
            return False

        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        if project.status != 'open':
            messages.warning(self.request, 'This project is not open for applications.')
            return False

        if ProjectApplication.objects.filter(
                project=project,
                student=self.request.user.student_profile
        ).exists():
            messages.warning(self.request, 'You have already applied to this project!')
            return False

        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.student = self.request.user.student_profile
        form.instance.status = 'pending'

        messages.success(
            self.request,
            f'Application submitted successfully to "{project.title}"!'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:my_applications')


class MyApplicationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View student's applications"""
    model = ProjectApplication
    template_name = 'projects/my_applications.html'
    context_object_name = 'applications'
    paginate_by = 10

    def test_func(self):
        return (self.request.user.user_type == 'student' and
                hasattr(self.request.user, 'student_profile'))

    def get_queryset(self):
        return ProjectApplication.objects.filter(
            student=self.request.user.student_profile
        ).select_related('project', 'project__company').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.request.user.student_profile
        qs = self.get_queryset()

        context['pending_count'] = qs.filter(status='pending').count()
        context['accepted_count'] = qs.filter(status='accepted').count()
        context['rejected_count'] = qs.filter(status='rejected').count()
        context['assigned_projects'] = student.assigned_projects.filter(
            status='in_progress'
        ).order_by('-created_at')

        return context


class ManageApplicationsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Company view to manage applications"""
    model = Project
    template_name = 'projects/manage_applications.html'
    context_object_name = 'project'

    def test_func(self):
        project = self.get_object()
        user = self.request.user

        # Allow if company owns the project
        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return project.company and project.company.user == user

        # Allow if university posted the project
        if user.user_type == 'university' and hasattr(user, 'university_profile'):
            return project.posted_by_university and project.university.user == user

        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        context['applications'] = project.applications.all().order_by('-created_at')
        context['pending_count'] = project.applications.filter(status='pending').count()
        context['accepted_count'] = project.applications.filter(status='accepted').count()
        context['rejected_count'] = project.applications.filter(status='rejected').count()

        return context


class ApplicationActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Accept or reject an application"""

    def test_func(self):
        application = get_object_or_404(ProjectApplication, pk=self.kwargs.get('application_id'))
        return (self.request.user.user_type == 'company' and
                hasattr(self.request.user, 'company_profile') and
                application.project.company.user == self.request.user)

    def post(self, request, pk, application_id):
        application = get_object_or_404(ProjectApplication, pk=application_id)
        project = application.project
        action = request.POST.get('action')

        if action == 'accept':
            with transaction.atomic():
                application.status = 'accepted'
                application.reviewed_at = timezone.now()
                application.save()

                project.assigned_students.add(application.student)

                if project.status == 'open':
                    project.status = 'in_progress'
                    project.save()

                messages.success(
                    request,
                    f'Accepted application from {application.student.user.get_full_name()}'
                )

        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_at = timezone.now()
            application.save()

            messages.warning(
                request,
                f'Rejected application from {application.student.user.get_full_name()}'
            )

        return redirect('projects:manage_applications', pk=project.pk)


class PendingReviewView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Projects pending university review"""
    model = Project
    template_name = 'projects/pending_review.html'
    context_object_name = 'projects'

    def test_func(self):
        return (self.request.user.user_type == 'university' and
                hasattr(self.request.user, 'university_profile'))

    def get_queryset(self):
        return Project.objects.filter(
            university=self.request.user.university_profile,
            status='pending_review'
        ).order_by('-submitted_for_review_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile
        context['pending_count'] = self.get_queryset().count()
        context['total_projects'] = profile.projects.count()
        return context


class ProjectReviewView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Approve or reject project (University only)"""

    def test_func(self):
        return (self.request.user.user_type == 'university' and
                hasattr(self.request.user, 'university_profile'))

    def post(self, request, pk):
        project = get_object_or_404(
            Project,
            pk=pk,
            university=request.user.university_profile
        )
        action = request.POST.get('action')

        if action == 'approve':
            project.status = 'open'
            project.approved_at = timezone.now()
            messages.success(request, f'Project "{project.title}" approved!')
        elif action == 'reject':
            project.status = 'rejected'
            project.rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
            messages.warning(request, f'Project "{project.title}" rejected.')

        project.save()
        return redirect('projects:pending_review')


class SubmitDeliverableView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Submit project deliverable (Student only)"""
    model = Deliverable
    form_class = DeliverableForm
    template_name = 'projects/submit_deliverable.html'

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return (self.request.user.user_type == 'student' and
                hasattr(self.request.user, 'student_profile') and
                self.request.user.student_profile in project.assigned_students.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.student = self.request.user.student_profile

        messages.success(self.request, 'Deliverable submitted successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'pk': self.kwargs['pk']})


# === MILESTONE & DELIVERABLE VIEWS ===

class ProjectWorkspaceView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Main project workspace showing milestones and deliverables"""
    model = Project
    template_name = 'projects/workspace.html'
    context_object_name = 'project'

    def test_func(self):
        project = self.get_object()
        user = self.request.user

        # Allow company/university who posted it, or assigned students
        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return project.company and project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return project.posted_by_university and project.university.user == user
        elif user.user_type == 'student' and hasattr(user, 'student_profile'):
            return user.student_profile in project.assigned_students.all()

        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # Get milestones
        context['milestones'] = project.milestones.all().order_by('order')

        # Get all deliverables
        context['deliverables'] = project.deliverables.all().order_by('-submitted_at')

        # Calculate progress
        total_milestones = project.milestones.count()
        approved_milestones = project.milestones.filter(status='approved').count()
        context['progress_percentage'] = (approved_milestones / total_milestones * 100) if total_milestones > 0 else 0

        return context


class ProjectMilestonesView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all milestones for a project"""
    model = Milestone
    template_name = 'projects/milestones.html'
    context_object_name = 'milestones'

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        user = self.request.user

        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return project.company and project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return project.university.user == user
        elif user.user_type == 'student' and hasattr(user, 'student_profile'):
            return user.student_profile in project.assigned_students.all()

        return False

    def get_queryset(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return project.milestones.all().order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context


class CreateMilestoneView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create milestone (Company/University only)"""
    model = Milestone
    form_class = MilestoneForm
    template_name = 'projects/create_milestone.html'

    def test_func(self):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        user = self.request.user

        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return project.company and project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return project.posted_by_university and project.university.user == user

        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = get_object_or_404(Project, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        form.instance.project = project

        # Auto-set order to be last
        max_order = project.milestones.aggregate(max_order=models.Max('order'))['max_order'] or 0
        form.instance.order = max_order + 1

        messages.success(self.request, 'Milestone created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('projects:workspace', kwargs={'pk': self.kwargs['pk']})


class UpdateMilestoneView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update milestone"""
    model = Milestone
    form_class = MilestoneForm
    template_name = 'projects/edit_milestone.html'

    def test_func(self):
        milestone = self.get_object()
        user = self.request.user

        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return milestone.project.company and milestone.project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return milestone.project.posted_by_university and milestone.project.university.user == user

        return False

    def get_success_url(self):
        return reverse_lazy('projects:workspace', kwargs={'pk': self.object.project.pk})


class ReviewDeliverableView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Company/University reviews and approves/rejects deliverable"""

    def test_func(self):
        deliverable = get_object_or_404(Deliverable, pk=self.kwargs.get('deliverable_id'))
        user = self.request.user

        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return deliverable.project.company and deliverable.project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return deliverable.project.posted_by_university and deliverable.project.university.user == user

        return False

    def get(self, request, pk, deliverable_id):
        project = get_object_or_404(Project, pk=pk)
        deliverable = get_object_or_404(Deliverable, pk=deliverable_id, project=project)

        return render(request, 'projects/review_deliverable.html', {
            'project': project,
            'deliverable': deliverable,
        })

    def post(self, request, pk, deliverable_id):
        project = get_object_or_404(Project, pk=pk)
        deliverable = get_object_or_404(Deliverable, pk=deliverable_id, project=project)

        action = request.POST.get('action')
        feedback = request.POST.get('feedback', '')

        if action == 'approve':
            deliverable.is_approved = True
            deliverable.revision_required = False
            deliverable.feedback = feedback
            deliverable.reviewed_at = timezone.now()
            deliverable.save()

            # Update milestone status if linked
            if deliverable.milestone:
                # Check if all deliverables for this milestone are approved
                milestone_deliverables = deliverable.milestone.deliverables.all()
                if all(d.is_approved for d in milestone_deliverables):
                    deliverable.milestone.status = 'approved'
                    deliverable.milestone.completed_at = timezone.now()
                    deliverable.milestone.save()

            messages.success(request, 'Deliverable approved!')

        elif action == 'revision':
            deliverable.is_approved = False
            deliverable.revision_required = True
            deliverable.feedback = feedback
            deliverable.reviewed_at = timezone.now()
            deliverable.save()

            if deliverable.milestone:
                deliverable.milestone.status = 'revision_required'
                deliverable.milestone.save()

            messages.warning(request, 'Revision requested for deliverable.')

        return redirect('projects:workspace', pk=project.pk)


class DeleteMilestoneView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete milestone"""
    model = Milestone
    template_name = 'projects/delete_milestone.html'

    def test_func(self):
        milestone = self.get_object()
        user = self.request.user

        if user.user_type == 'company' and hasattr(user, 'company_profile'):
            return milestone.project.company and milestone.project.company.user == user
        elif user.user_type == 'university' and hasattr(user, 'university_profile'):
            return milestone.project.posted_by_university and milestone.project.university.user == user

        return False

    def get_success_url(self):
        return reverse_lazy('projects:workspace', kwargs={'pk': self.object.project.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Milestone deleted successfully!')
        return super().delete(request, *args, **kwargs)


class UniversityApplicationsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """University view to manage applications to THEIR OWN projects"""
    model = ProjectApplication
    template_name = 'projects/university_applications.html'
    context_object_name = 'applications'
    paginate_by = 20

    def test_func(self):
        """Only allow universities"""
        return (self.request.user.user_type == 'university' and
                hasattr(self.request.user, 'university_profile'))

    def get_queryset(self):
        """Get applications to university's own projects"""
        university = self.request.user.university_profile

        # Get applications to projects posted BY this university
        queryset = ProjectApplication.objects.filter(
            project__university=university,
            project__posted_by_university=True  # Only their own projects
        ).select_related(
            'student',
            'student__user',
            'project'
        ).order_by('-created_at')

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        university = self.request.user.university_profile

        # Get all applications to university's projects
        all_apps = ProjectApplication.objects.filter(
            project__university=university,
            project__posted_by_university=True
        )

        # Stats
        context['pending_count'] = all_apps.filter(status='pending').count()
        context['accepted_count'] = all_apps.filter(status='accepted').count()
        context['rejected_count'] = all_apps.filter(status='rejected').count()
        context['total_count'] = all_apps.count()

        # Current filter
        context['current_status'] = self.request.GET.get('status', 'all')

        return context


class UniversityApplicationActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """University accepts or rejects applications to their own projects"""

    def test_func(self):
        """Verify university owns this project"""
        application = get_object_or_404(ProjectApplication, pk=self.kwargs.get('application_id'))
        return (self.request.user.user_type == 'university' and
                hasattr(self.request.user, 'university_profile') and
                application.project.posted_by_university and
                application.project.university.user == self.request.user)

    def post(self, request, application_id):
        application = get_object_or_404(ProjectApplication, pk=application_id)
        project = application.project
        action = request.POST.get('action')

        if action == 'accept':
            with transaction.atomic():
                application.status = 'accepted'
                application.reviewed_at = timezone.now()
                application.save()

                # Add student to assigned students
                project.assigned_students.add(application.student)

                # If project was open, mark as in progress
                if project.status == 'open':
                    project.status = 'in_progress'
                    project.save()

                messages.success(
                    request,
                    f'✓ Accepted application from {application.student.user.get_full_name()}'
                )

        elif action == 'reject':
            application.status = 'rejected'
            application.reviewed_at = timezone.now()
            application.save()

            messages.warning(
                request,
                f'✗ Rejected application from {application.student.user.get_full_name()}'
            )

        elif action == 'shortlist':
            application.status = 'shortlisted'
            application.save()

            messages.info(
                request,
                f'⭐ Shortlisted application from {application.student.user.get_full_name()}'
            )

        # Redirect back to applications page
        return redirect('projects:university_applications')

