# apps/projects/forms.py - ROBUST FINAL VERSION
"""
Purpose: Project-related forms
Contains:

ProjectForm (create/edit projects)
ProjectApplicationForm (apply to projects)
MilestoneForm (create milestones)
DeliverableForm (submit work)
"""
from django import forms
from .models import Project, ProjectApplication, Deliverable, Milestone
from ..accounts.models import University


class ProjectForm(forms.ModelForm):
    # Department and Year choices
    DEPARTMENT_CHOICES = [
        ('computer_science', 'Computer Science'),
        ('information_technology', 'Information Technology'),
        ('electronics', 'Electronics & Communication'),
        ('mechanical', 'Mechanical Engineering'),
        ('civil', 'Civil Engineering'),
        ('electrical', 'Electrical Engineering'),
        ('chemical', 'Chemical Engineering'),
        ('biotechnology', 'Biotechnology'),
        ('mba', 'MBA'),
        ('bba', 'BBA'),
        ('bcom', 'B.Com'),
        ('bca', 'BCA'),
        ('mca', 'MCA'),
        ('design', 'Design'),
        ('architecture', 'Architecture'),
        ('data_science', 'Data Science'),
        ('ai_ml', 'AI & Machine Learning'),
    ]

    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
        ('graduate', 'Graduate/Masters'),
    ]

    # Custom multi-select fields (NOT part of model)
    eligible_departments_list = forms.MultipleChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Eligible Departments",
        help_text="Select all departments eligible for this project (leave blank for all)"
    )

    eligible_years_list = forms.MultipleChoiceField(
        choices=YEAR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Eligible Years",
        help_text="Select eligible years (leave blank for all years)"
    )

    class Meta:
        model = Project
        fields = [
            'university',
            'title', 'domain', 'description',
            'required_skills', 'team_type', 'team_size',
            'job_type',
            'min_gpa',
            'payment_amount', 'payment_type',
            'duration_weeks', 'deadline',
            'attachment'
        ]

        labels = {
            'deadline': 'Project Closure Date',
            'payment_amount': 'Remuneration Amount (₹)',
            'payment_type': 'Remuneration Type',
            'attachment': 'Job Description (JD)',
            'job_type': 'Work Location Type',
        }

        help_texts = {
            'deadline': 'Final date for project completion',
            'payment_amount': 'Total remuneration for the project',
            'attachment': 'Upload the detailed job description document (PDF, DOC)',
            'job_type': 'Specify if the work is Remote, Hybrid, or On-site',
            'payment_type': 'Fixed: Pay full amount at end. Milestone: Pay in installments',
        }

        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Provide detailed project description...',
                'class': 'form-control'
            }),
            'required_skills': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Python, Django, React (comma-separated)',
                'class': 'form-control'
            }),
            'deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'payment_amount': forms.NumberInput(attrs={
                'placeholder': 'e.g., 15000',
                'class': 'form-control'
            }),
            'duration_weeks': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'min_gpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '10'
            }),
            'team_size': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'university': forms.Select(attrs={
                'class': 'form-select'
            }),
            'domain': forms.Select(attrs={
                'class': 'form-select'
            }),
            'team_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'job_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show verified universities
        self.fields['university'].queryset = University.objects.filter(is_verified=True)

        # If editing existing project, populate the custom fields
        if self.instance and self.instance.pk:
            # Convert eligible_departments from "dept1,dept2" to ['dept1', 'dept2']
            if self.instance.eligible_departments:
                dept_list = [d.strip() for d in self.instance.eligible_departments.split(',') if d.strip()]
                self.initial['eligible_departments_list'] = dept_list

            # Convert eligible_years from "1,2,3" to ['1', '2', '3']
            if self.instance.eligible_years:
                year_list = [y.strip() for y in self.instance.eligible_years.split(',') if y.strip()]
                self.initial['eligible_years_list'] = year_list

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Convert multi-select fields back to comma-separated strings
        departments = self.cleaned_data.get('eligible_departments_list')
        if departments:
            instance.eligible_departments = ','.join(departments)
        else:
            instance.eligible_departments = ''

        years = self.cleaned_data.get('eligible_years_list')
        if years:
            instance.eligible_years = ','.join(years)
        else:
            instance.eligible_years = ''

        if commit:
            instance.save()
        return instance


class ProjectApplicationForm(forms.ModelForm):
    class Meta:
        model = ProjectApplication
        fields = [
            'cover_letter', 'proposed_approach',
            'portfolio_links', 'is_team_application',
            'team_members'
        ]
        widgets = {
            'cover_letter': forms.Textarea(
                attrs={'rows': 4, 'placeholder': 'Explain why you are a good fit...', 'class': 'form-control'}),
            'proposed_approach': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'How would you approach this project?', 'class': 'form-control'}),
            'portfolio_links': forms.Textarea(
                attrs={'rows': 2, 'placeholder': 'Links to relevant work', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['team_members'].required = False


class DeliverableForm(forms.ModelForm):
    class Meta:
        model = Deliverable
        fields = ['title', 'description', 'file', 'submission_notes', 'milestone']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'submission_notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'milestone': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if self.project:
            self.fields['milestone'].queryset = self.project.milestones.all()
            self.fields['milestone'].required = False


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'description', 'payment_percentage', 'due_date']

        labels = {
            'payment_percentage': 'Remuneration Percentage (%)',
            'due_date': 'Milestone Closure Date',
        }

        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

    def clean_payment_percentage(self):
        percentage = self.cleaned_data.get('payment_percentage')
        if percentage is not None:
            if percentage < 0 or percentage > 100:
                raise forms.ValidationError('Percentage must be between 0 and 100')
        return percentage