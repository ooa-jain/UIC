"""
Purpose: Registration and profile editing forms
Contains:

StudentRegistrationForm
CompanyRegistrationForm
UniversityRegistrationForm
StudentProfileForm
CompanyProfileForm
UniversityProfileForm
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import User, Student, Company, University


# this basically takes care of the user registration forms for each type of user

class StudentRegistrationForm(UserCreationForm):
    """Student registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_tag = False

    def clean(self):
        cleaned_data = super().clean()
        if not University.objects.exists():
            raise forms.ValidationError(
                "No university is registered yet. Please contact the administrator."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # Create incomplete profile - student must complete it
            Student.objects.create(
                user=user,
                university=None,  # Student will select
                student_id='',  # Student will fill
                department='Not specified',
                year='1',
                skills='',
                preferred_domains='',
                is_verified=False,
                verification_status='pending'
            )
        return user
# apps/accounts/forms.py - UPDATE CompanyRegistrationForm

class CompanyRegistrationForm(UserCreationForm):
    """Company registration form"""
    email = forms.EmailField(required=True, help_text="Official company email")
    company_name = forms.CharField(max_length=200, required=True, label="Company Name")
    industry = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False, help_text="Company website")
    contact_person = forms.CharField(max_length=100, required=True, label="SPOC Name",
                                    help_text="Single Point of Contact")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register as Company', css_class='btn-primary w-100'))

    def clean(self):
        cleaned_data = super().clean()
        if not University.objects.filter(is_verified=True).exists():
            raise forms.ValidationError(
                "⚠️ No verified universities are available yet. "
                "Please contact the platform administrator."
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'company'
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            Company.objects.create(
                user=user,
                name=self.cleaned_data['company_name'],
                industry=self.cleaned_data['industry'],
                website=self.cleaned_data.get('website', ''),
                description='',
                contact_person=self.cleaned_data['contact_person'],
                contact_email=self.cleaned_data['email'],
                contact_phone='',
                address='',
                is_verified=False,
                verification_status='pending'
            )
        return user


class UniversityRegistrationForm(UserCreationForm):
    """University admin registration form"""
    email = forms.EmailField(required=True)
    university_name = forms.CharField(max_length=200, required=True, label="University Name")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=True)
    admin_name = forms.CharField(max_length=100, required=True, label="Admin Name")
    admin_phone = forms.CharField(max_length=15, required=True, label="Admin Phone")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register as University', css_class='btn-primary w-100'))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'university'
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            University.objects.create(
                user=user,
                name=self.cleaned_data['university_name'],
                address=self.cleaned_data['address'],
                admin_name=self.cleaned_data['admin_name'],
                admin_email=self.cleaned_data['email'],
                admin_phone=self.cleaned_data['admin_phone']
            )
        return user


# ============ PROFILE EDIT FORMS ============
# apps/accounts/forms.py - UPDATE StudentProfileForm

class StudentProfileForm(forms.ModelForm):
    """Student profile editing form"""

    class Meta:
        model = Student
        fields = [
            'university',  # NEW: Allow student to select university
            'student_id', 'department', 'year', 'gpa',
            'university_email',  # NEW
            'bio', 'profile_picture', 'resume', 'portfolio_url',
            'skills', 'preferred_domains', 'available_for_projects'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Python, Django, React, UI/UX Design (comma-separated)'
            }),
            'preferred_domains': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Coding, Design, Marketing (comma-separated)'
            }),
            'university_email': forms.EmailInput(attrs={
                'placeholder': 'jupg+ uniquecode@youruniversity.ac.in'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        # Only show verified universities
        self.fields['university'].queryset = University.objects.filter(is_verified=True)

        # Make university_email required
        self.fields['university_email'].required = True

        self.helper.layout = Layout(
            Row(
                Column('university', css_class='col-md-12'),
            ),
            Row(
                Column('student_id', css_class='col-md-6'),
                Column('university_email', css_class='col-md-6'),
            ),
            Row(
                Column('department', css_class='col-md-6'),
                Column('year', css_class='col-md-6'),
            ),
            Row(
                Column('gpa', css_class='col-md-12'),
            ),
            'bio',
            Row(
                Column('profile_picture', css_class='col-md-6'),
                Column('resume', css_class='col-md-6'),
            ),
            'portfolio_url',
            'skills',
            'preferred_domains',
            'available_for_projects',
            Submit('submit', 'Submit for Verification', css_class='btn-primary')
        )


# apps/accounts/forms.py - UPDATE CompanyProfileForm

class CompanyProfileForm(forms.ModelForm):
    """Company profile editing form"""

    class Meta:
        model = Company
        fields = [
            'name', 'logo', 'industry', 'website', 'description',
            'contact_person', 'contact_email', 'contact_phone', 'address',
            'company_registration_number', 'gst_number',  # NEW
            'verification_document'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'contact_email': forms.EmailInput(attrs={
                'placeholder': 'official@company.com',
                'help_text': 'Use official company email'
            }),
            'company_registration_number': forms.TextInput(attrs={
                'placeholder': 'CIN/Registration Number'
            }),
            'gst_number': forms.TextInput(attrs={
                'placeholder': 'GST Number (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('logo', css_class='col-md-4'),
            ),
            Row(
                Column('industry', css_class='col-md-6'),
                Column('website', css_class='col-md-6'),
            ),
            'description',
            Row(
                Column('contact_person', css_class='col-md-6'),
                Column('contact_email', css_class='col-md-6'),
            ),
            Row(
                Column('contact_phone', css_class='col-md-6'),
                Column('address', css_class='col-md-6'),
            ),
            Row(
                Column('company_registration_number', css_class='col-md-6'),
                Column('gst_number', css_class='col-md-6'),
            ),
            'verification_document',
            Submit('submit', 'Submit for Verification', css_class='btn-primary')
        )

        # Make these fields required
        self.fields['contact_email'].required = True
        self.fields['contact_person'].required = True
        self.fields['company_registration_number'].required = True
class UniversityProfileForm(forms.ModelForm):
    """University profile editing form"""

    class Meta:
        model = University
        fields = [
            'name', 'logo', 'address', 'website', 'description',
            'admin_name', 'admin_email', 'admin_phone',
            'auto_approve_projects', 'min_payment_amount'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('logo', css_class='col-md-4'),
            ),
            'website',
            'description',
            'address',
            Row(
                Column('admin_name', css_class='col-md-6'),
                Column('admin_email', css_class='col-md-6'),
            ),
            'admin_phone',
            Row(
                Column('auto_approve_projects', css_class='col-md-6'),
                Column('min_payment_amount', css_class='col-md-6'),
            ),
            Submit('submit', 'Save Profile', css_class='btn-primary')
        )