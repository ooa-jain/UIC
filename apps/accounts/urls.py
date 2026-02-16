# apps/accounts/urls.py
"""
Purpose: Account-related URL patterns
Routes:

/accounts/login/ - Login
/accounts/register/ - Registration
/accounts/dashboard/ - Main dashboard
/accounts/profile/ - View profile
/accounts/profile/edit/ - Edit profile
/accounts/university/students/ - Manage students
/accounts/university/companies/ - Manage companies
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),

    # Main Dashboard (auto-redirects based on user type)
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Profile Management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),

    # === TYPE-SPECIFIC ADMIN/MANAGEMENT URLS ===

    # University Admin URLs
    path('university/dashboard/', views.UniversityDashboardView.as_view(), name='university_dashboard'),
    path('university/students/', views.UniversityStudentsView.as_view(), name='university_students'),
    path('university/companies/', views.UniversityCompaniesView.as_view(), name='university_companies'),
    path('university/companies/<int:company_id>/verify/',
         views.CompanyVerificationActionView.as_view(),
         name='company_verification_action'),

    path('university/projects/', views.UniversityProjectsView.as_view(), name='university_projects'),  # NEW
    path('university/students/', views.UniversityStudentsView.as_view(), name='university_students'),
    path('university/students/<int:student_id>/verify/',views.StudentVerificationActionView.as_view(),name='student_verification_action'),
    # Company Admin URLs
    path('company/dashboard/', views.CompanyDashboardView.as_view(), name='company_dashboard'),
    path('company/projects/', views.CompanyProjectsView.as_view(), name='company_projects'),

    # Student URLs
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),

    # Public Profiles
    path('company/<int:pk>/', views.CompanyPublicProfileView.as_view(), name='company_public'),
    path('student/<int:pk>/', views.StudentPublicProfileView.as_view(), name='student_public'),
]