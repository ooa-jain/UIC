"""
Purpose: All account-related views
Contains:

RegisterView
ProfileView
ProfileEditView
DashboardView (redirects based on user type)
UniversityDashboardView
UniversityStudentsView
UniversityCompaniesView
StudentVerificationActionView
CompanyVerificationActionView
CompanyDashboardView
StudentDashboardView
"""
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, View, ListView
from django.urls import reverse_lazy
from django.http import Http404
from .models import User, Student, Company, University
from .forms import (
    StudentRegistrationForm, CompanyRegistrationForm,
    UniversityRegistrationForm, StudentProfileForm,
    CompanyProfileForm, UniversityProfileForm
)
from ..projects.models import Project


class RegisterView(View):
    """User registration view with role selection"""
    template_name = 'accounts/register.html'

    def get_form_class(self, user_type):
        form_map = {
            'student': StudentRegistrationForm,
            'company': CompanyRegistrationForm,
            'university': UniversityRegistrationForm,
        }
        return form_map.get(user_type, StudentRegistrationForm)

    def get(self, request):
        user_type = request.GET.get('type', 'student')
        form_class = self.get_form_class(user_type)
        form = form_class()
        return render(request, self.template_name, {
            'form': form,
            'user_type': user_type
        })

    # apps/accounts/views.py - UPDATE RegisterView post method

    def post(self, request):
        user_type = request.GET.get('type', 'student')
        form_class = self.get_form_class(user_type)
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            try:
                user = form.save()
                login(request, user)

                # Redirect based on user type
                if user_type == 'student':
                    messages.info(request, 'Please complete your profile to get verified by your university.')
                    return redirect('accounts:profile_edit')
                elif user_type == 'company':
                    messages.info(request, 'Please complete your company profile for university verification.')
                    return redirect('accounts:profile_edit')
                else:
                    messages.success(request, 'Registration successful!')
                    return redirect('accounts:dashboard')

            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')

        return render(request, self.template_name, {
            'form': form,
            'user_type': user_type
        })

class ProfileView(LoginRequiredMixin, DetailView):
    """View user profile"""
    template_name = 'accounts/profile.html'

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.user_type == 'student':
            context['profile'] = getattr(user, 'student_profile', None)
        elif user.user_type == 'company':
            context['profile'] = getattr(user, 'company_profile', None)
        elif user.user_type == 'university':
            context['profile'] = getattr(user, 'university_profile', None)

        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        user = self.request.user
        try:
            if user.user_type == 'student':
                return Student.objects.get(user=user)
            elif user.user_type == 'company':
                return Company.objects.get(user=user)
            elif user.user_type == 'university':
                return University.objects.get(user=user)
        except (Student.DoesNotExist, Company.DoesNotExist, University.DoesNotExist):
            messages.error(self.request, 'Profile not found. Please contact support.')
            return None
        return None

    def get_form_class(self):
        user = self.request.user
        form_map = {
            'student': StudentProfileForm,
            'company': CompanyProfileForm,
            'university': UniversityProfileForm,
        }
        return form_map.get(user.user_type)

    def form_valid(self, form):
        profile = form.save(commit=False)

        # For students, set verification status to pending after profile completion
        if self.request.user.user_type == 'student':
            if not profile.is_verified:
                profile.verification_status = 'pending'
                messages.success(
                    self.request,
                    'Profile submitted for verification! Your university will review and approve your account.'
                )
            else:
                messages.success(self.request, 'Profile updated successfully!')
        else:
            messages.success(self.request, 'Profile updated successfully!')

        profile.save()
        return super().form_valid(form)


# apps/accounts/views.py - UPDATE DashboardView

class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard - shows different content based on user type"""

    def get_template_names(self):
        user_type = self.request.user.user_type
        template_map = {
            'student': 'dashboard/student.html',
            'company': 'dashboard/company.html',
            'university': 'dashboard/university.html',
        }
        return [template_map.get(user_type, 'dashboard/student.html')]

    # apps/accounts/views.py - UPDATE DashboardView dispatch method

    def dispatch(self, request, *args, **kwargs):
        """Verify user has proper profile and verification status"""
        if request.user.is_authenticated:
            user = request.user

            # Check student verification
            if user.user_type == 'student':
                if not hasattr(user, 'student_profile'):
                    messages.error(request, 'Profile not found. Please contact support.')
                    return redirect('home')

                student = user.student_profile

                if not student.university or not student.student_id or not student.university_email:
                    messages.warning(
                        request,
                        '⚠️ Please complete your profile with university details to get verified.'
                    )
                    return redirect('accounts:profile_edit')

                if student.verification_status == 'pending':
                    return render(request, 'accounts/verification_pending.html', {
                        'student': student
                    })
                elif student.verification_status == 'rejected':
                    return render(request, 'accounts/verification_rejected.html', {
                        'student': student
                    })

            # NEW: Check company verification
            elif user.user_type == 'company':
                if not hasattr(user, 'company_profile'):
                    messages.error(request, 'Profile not found. Please contact support.')
                    return redirect('home')

                company = user.company_profile

                # Check if profile is incomplete
                if (not company.contact_email or not company.contact_person or
                        not company.company_registration_number or not company.verification_document):
                    messages.warning(
                        request,
                        '⚠️ Please complete your company profile and upload verification documents.'
                    )
                    return redirect('accounts:profile_edit')

                # Check verification status
                if company.verification_status == 'pending':
                    return render(request, 'accounts/company_verification_pending.html', {
                        'company': company
                    })
                elif company.verification_status == 'rejected':
                    return render(request, 'accounts/company_verification_rejected.html', {
                        'company': company
                    })

        return super().dispatch(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.user_type == 'student':
            profile = user.student_profile
            context.update({
                'profile': profile,
                'active_projects': profile.assigned_projects.filter(status='in_progress').count(),
                'completed_projects': profile.projects_completed,
                'pending_applications': profile.applications.filter(status='pending').count(),
                'total_earned': profile.total_earned,
            })

        elif user.user_type == 'company':
            profile = user.company_profile
            context.update({
                'profile': profile,
                'active_projects': profile.projects.filter(status__in=['open', 'in_progress']).count(),
                'pending_review': profile.projects.filter(status='pending_review').count(),
                'total_projects': profile.total_projects_posted,
                'rating': profile.rating,
            })

        elif user.user_type == 'university':
            profile = user.university_profile
            context.update({
                'profile': profile,
                'pending_projects': profile.projects.filter(status='pending_review').count(),
                'active_projects': profile.projects.filter(status__in=['open', 'in_progress']).count(),
                'total_students': profile.students.count(),
                'verified_companies': profile.verified_companies.count(),
            })

        return context
# Mixins for role-based access control
class StudentRequiredMixin(UserPassesTestMixin):
    """Only allow students"""

    def test_func(self):
        return (self.request.user.is_authenticated and
                self.request.user.user_type == 'student' and
                hasattr(self.request.user, 'student_profile'))


class CompanyRequiredMixin(UserPassesTestMixin):
    """Only allow companies"""

    def test_func(self):
        return (self.request.user.is_authenticated and
                self.request.user.user_type == 'company' and
                hasattr(self.request.user, 'company_profile'))


class UniversityRequiredMixin(UserPassesTestMixin):
    """Only allow university admins"""

    def test_func(self):
        return (self.request.user.is_authenticated and
                self.request.user.user_type == 'university' and
                hasattr(self.request.user, 'university_profile'))


class CompanyPublicProfileView(DetailView):
    """View company's public profile"""
    model = Company
    template_name = 'accounts/company_public.html'
    context_object_name = 'company'


class StudentPublicProfileView(DetailView):
    """View student's public profile"""
    model = Student
    template_name = 'accounts/student_public.html'
    context_object_name = 'student'


#TYPE-SPECIFIC DASHBOARD VIEWS

class UniversityDashboardView(LoginRequiredMixin, UniversityRequiredMixin, TemplateView):
    """University-specific admin dashboard"""
    template_name = 'dashboard/university.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile

        context.update({
            'profile': profile,
            'pending_projects': profile.projects.filter(status='pending_review').count(),
            'active_projects': profile.projects.filter(status__in=['open', 'in_progress']).count(),
            'total_students': profile.students.count(),
            'verified_companies': profile.verified_companies.count(),
            'recent_projects': profile.projects.order_by('-created_at')[:10],

            # NEW: Add pending students count
            'pending_students_count': profile.students.filter(verification_status='pending').count(),
        })
        return context




class UniversityCompaniesView(LoginRequiredMixin, UniversityRequiredMixin, TemplateView):
    """University view to manage/verify companies"""
    template_name = 'accounts/university_companies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile
        context['verified_companies'] = profile.verified_companies.all()
        context['all_companies'] = Company.objects.all()
        return context


class UniversityProjectsView(LoginRequiredMixin, UniversityRequiredMixin, ListView):
    """University view to see ONLY their own posted projects"""
    model = Project
    template_name = 'accounts/university_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        """Return only projects posted BY this university"""
        university = self.request.user.university_profile

        # Only projects posted BY this university (not company projects)
        queryset = Project.objects.filter(
            university=university,
            posted_by_university=True  # Only university's own projects
        ).order_by('-created_at')

        # Apply status filter if provided
        status_filter = self.request.GET.get('status', 'all')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        university = self.request.user.university_profile

        # Get all projects posted BY this university (for stats)
        all_university_projects = Project.objects.filter(
            university=university,
            posted_by_university=True
        )

        # Add stats
        context['total_count'] = all_university_projects.count()
        context['pending_count'] = all_university_projects.filter(status='pending_review').count()
        context['open_count'] = all_university_projects.filter(status='open').count()
        context['in_progress_count'] = all_university_projects.filter(status='in_progress').count()
        context['completed_count'] = all_university_projects.filter(status='completed').count()
        context['rejected_count'] = all_university_projects.filter(status='rejected').count()

        # Current filter
        context['current_filter'] = self.request.GET.get('status', 'all')

        return context


# NEW VIEW: University Students Management with Verification
class UniversityStudentsView(LoginRequiredMixin, UniversityRequiredMixin, TemplateView):
    """University view to manage and verify students"""
    template_name = 'accounts/university_students.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile

        # Get filter
        status_filter = self.request.GET.get('status', 'all')

        students = profile.students.all()

        if status_filter == 'pending':
            students = students.filter(verification_status='pending')
        elif status_filter == 'approved':
            students = students.filter(verification_status='approved')
        elif status_filter == 'rejected':
            students = students.filter(verification_status='rejected')

        context['students'] = students.order_by('-created_at')
        context['current_filter'] = status_filter
        context['pending_count'] = profile.students.filter(verification_status='pending').count()
        context['approved_count'] = profile.students.filter(verification_status='approved').count()
        context['rejected_count'] = profile.students.filter(verification_status='rejected').count()
        context['total_count'] = profile.students.count()

        return context


class StudentVerificationActionView(LoginRequiredMixin, UniversityRequiredMixin, View):
    """University approves or rejects student verification"""

    def post(self, request, student_id):
        university = request.user.university_profile
        student = get_object_or_404(Student, pk=student_id, university=university)

        action = request.POST.get('action')

        if action == 'approve':
            student.is_verified = True
            student.verification_status = 'approved'
            student.verified_by = university
            student.verified_at = datetime.now()
            student.save()

            messages.success(
                request,
                f'✓ Approved {student.user.get_full_name()} - Student can now access all features.'
            )

        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
            student.is_verified = False
            student.verification_status = 'rejected'
            student.rejection_reason = rejection_reason
            student.save()

            messages.warning(
                request,
                f'✗ Rejected {student.user.get_full_name()}'
            )

        return redirect('accounts:university_students')


class CompanyDashboardView(LoginRequiredMixin, CompanyRequiredMixin, TemplateView):
    """Company-specific admin dashboard"""
    template_name = 'dashboard/company.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.company_profile
        context.update({
            'profile': profile,
            'active_projects': profile.projects.filter(status__in=['open', 'in_progress']).count(),
            'pending_review': profile.projects.filter(status='pending_review').count(),
            'total_projects': profile.total_projects_posted,
            'rating': profile.rating,
            'recent_projects': profile.projects.order_by('-created_at')[:10],
        })
        return context


class CompanyDashboardView(LoginRequiredMixin, CompanyRequiredMixin, TemplateView):
    """Company-specific admin dashboard"""
    template_name = 'dashboard/company.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.company_profile

        # Get all company projects
        all_projects = profile.projects.all()

        # Calculate stats correctly
        context.update({
            'profile': profile,
            'active_projects': all_projects.filter(status='in_progress').count(),  # Only in_progress
            'pending_review': all_projects.filter(status='pending_review').count(),  # Only pending_review
            'total_projects': all_projects.count(),  # Total
            'rating': profile.rating,
            'recent_projects': all_projects.order_by('-created_at')[:10],

            # Add additional stats
            'open_projects': all_projects.filter(status='open').count(),
            'completed_projects': all_projects.filter(status='completed').count(),
        })
        return context

class CompanyProjectsView(LoginRequiredMixin, CompanyRequiredMixin, ListView):
    """Company view to see only their own projects"""
    model = Project
    template_name = 'accounts/company_projects.html'
    context_object_name = 'projects'
    paginate_by = 10

    def get_queryset(self):
        """Return only this company's projects, filtered by status if provided"""
        # Start with only this company's projects
        queryset = Project.objects.filter(
            company=self.request.user.company_profile
        ).order_by('-created_at')

        # Apply status filter if provided
        status_filter = self.request.GET.get('status', 'all')
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.company_profile

        # Get all projects for this company (for stats)
        all_company_projects = Project.objects.filter(company=profile)

        # Add stats
        context['total_count'] = all_company_projects.count()
        context['pending_count'] = all_company_projects.filter(status='pending_review').count()
        context['open_count'] = all_company_projects.filter(status='open').count()
        context['in_progress_count'] = all_company_projects.filter(status='in_progress').count()
        context['completed_count'] = all_company_projects.filter(status='completed').count()
        context['rejected_count'] = all_company_projects.filter(status='rejected').count()

        # Current filter
        context['current_filter'] = self.request.GET.get('status', 'all')

        return context



class CompanyProjectsView(LoginRequiredMixin, CompanyRequiredMixin, TemplateView):
    """Company view to manage their projects"""
    template_name = 'accounts/company_projects.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.company_profile
        context['projects'] = profile.projects.all().order_by('-created_at')
        return context

class StudentDashboardView(LoginRequiredMixin, StudentRequiredMixin, TemplateView):
    """Student-specific dashboard"""
    template_name = 'dashboard/student.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.student_profile
        context.update({
            'profile': profile,
            'active_projects': profile.assigned_projects.filter(status='in_progress').count(),
            'completed_projects': profile.projects_completed,
            'pending_applications': profile.applications.filter(status='pending').count(),
            'total_earned': profile.total_earned,
        })
        return context


# apps/accounts/views.py - ADD this new view

class UniversityCompaniesView(LoginRequiredMixin, UniversityRequiredMixin, TemplateView):
    """University view to manage/verify companies"""
    template_name = 'accounts/university_companies.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile

        # Get filter
        status_filter = self.request.GET.get('status', 'all')

        # Get ALL companies, not just verified ones
        companies = Company.objects.all()

        if status_filter == 'pending':
            companies = companies.filter(verification_status='pending')
        elif status_filter == 'approved':
            companies = companies.filter(verification_status='approved', verified_by=profile)
        elif status_filter == 'rejected':
            companies = companies.filter(verification_status='rejected')

        context['companies'] = companies.order_by('-created_at')
        context['current_filter'] = status_filter
        context['pending_count'] = Company.objects.filter(verification_status='pending').count()
        context['approved_count'] = profile.verified_companies.filter(verification_status='approved').count()
        context['rejected_count'] = Company.objects.filter(verification_status='rejected').count()
        context['total_count'] = Company.objects.count()

        return context


class CompanyVerificationActionView(LoginRequiredMixin, UniversityRequiredMixin, View):
    """University approves or rejects company verification"""

    def post(self, request, company_id):
        university = request.user.university_profile
        company = get_object_or_404(Company, pk=company_id)

        action = request.POST.get('action')

        if action == 'approve':
            company.is_verified = True
            company.verification_status = 'approved'
            company.verified_by = university
            company.verified_at = datetime.now()
            company.save()

            messages.success(
                request,
                f'✓ Approved {company.name} - Company can now post projects.'
            )

        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', 'No reason provided')
            company.is_verified = False
            company.verification_status = 'rejected'
            company.rejection_reason = rejection_reason
            company.save()

            messages.warning(
                request,
                f'✗ Rejected {company.name}'
            )

        return redirect('accounts:university_companies')