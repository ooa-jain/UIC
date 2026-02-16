"""
Purpose: Django admin panel configuration
Registers: User, Student, Company, University
"""


from django.contrib import admin
from .models import User, Student, Company, University


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'department', 'year', 'gpa']
    list_filter = ['year', 'department']  # removed is_active
    search_fields = ['user__username', 'student_id']
    raw_id_fields = ['user', 'university']


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'admin_email', 'admin_phone', 'is_verified']
    list_filter = ['is_verified']  # removed is_active
    search_fields = ['name', 'admin_email']
    raw_id_fields = ['user']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'contact_email', 'is_verified']
    list_filter = ['industry', 'is_verified']
    search_fields = ['name', 'contact_email']
    raw_id_fields = ['user', 'verified_by']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'user_type', 'email']
    list_filter = ['user_type']
    search_fields = ['username', 'email']
