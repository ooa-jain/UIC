# apps/accounts/views.py - REPLACE ENTIRE FILE

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, View
from django.urls import reverse_lazy
from django.http import Http404
from .models import User, Student, Company, University
from .forms import (
    StudentRegistrationForm, CompanyRegistrationForm,
    UniversityRegistrationForm, StudentProfileForm,
    CompanyProfileForm, UniversityProfileForm
)


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

    def post(self, request):
        user_type = request.GET.get('type', 'student')
        form_class = self.get_form_class(user_type)
        form = form_class(request.POST, request.FILES)

        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, 'Registration successful! Please complete your profile.')
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
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


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

    def dispatch(self, request, *args, **kwargs):
        """Verify user has proper profile before showing dashboard"""
        if request.user.is_authenticated:
            user = request.user
            profile_exists = False

            if user.user_type == 'student':
                profile_exists = hasattr(user, 'student_profile')
            elif user.user_type == 'company':
                profile_exists = hasattr(user, 'company_profile')
            elif user.user_type == 'university':
                profile_exists = hasattr(user, 'university_profile')

            if not profile_exists:
                messages.warning(request, 'Your profile is incomplete. Please contact support.')
                return redirect('home')

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


# ============ TYPE-SPECIFIC DASHBOARD VIEWS ============

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
        })
        return context


class UniversityStudentsView(LoginRequiredMixin, UniversityRequiredMixin, TemplateView):
    """University view to manage students"""
    template_name = 'accounts/university_students.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.university_profile
        context['students'] = profile.students.all().order_by('-created_at')
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