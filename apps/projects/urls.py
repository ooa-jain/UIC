"""
Purpose: Project-related URL patterns
Routes:

/projects/ - List all projects
/projects/<id>/ - Project details
/projects/create/ - Create project
/projects/<id>/apply/ - Apply to project
/projects/my-applications/ - View applications
"""
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Project listing and details
    path('', views.ProjectListView.as_view(), name='list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),

    # Company/University - Project CRUD
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='delete'),

    # Student - Applications
    path('<int:pk>/apply/', views.ProjectApplyView.as_view(), name='apply'),
    path('my-applications/', views.MyApplicationsView.as_view(), name='my_applications'),

    # Company/University - Application management
    path('<int:pk>/applications/', views.ManageApplicationsView.as_view(), name='manage_applications'),
    path('<int:pk>/applications/<int:application_id>/action/', views.ApplicationActionView.as_view(),
         name='application_action'),

    # ADD THESE TWO NEW LINES ↓
    # University - Application Review (for their own projects)
    path('university/applications/', views.UniversityApplicationsView.as_view(),
         name='university_applications'),
    path('university/applications/<int:application_id>/action/',
         views.UniversityApplicationActionView.as_view(),
         name='university_application_action'),
    # ↑ END OF NEW LINES


    # University - Review
    path('pending-review/', views.PendingReviewView.as_view(), name='pending_review'),
    path('<int:pk>/review/', views.ProjectReviewView.as_view(), name='review'),

    # Project Workspace (after student is accepted)
    path('<int:pk>/workspace/', views.ProjectWorkspaceView.as_view(), name='workspace'),

    # Milestones
    path('<int:pk>/milestones/', views.ProjectMilestonesView.as_view(), name='milestones'),
    path('<int:pk>/milestone/create/', views.CreateMilestoneView.as_view(), name='create_milestone'),
    path('milestone/<int:pk>/edit/', views.UpdateMilestoneView.as_view(), name='edit_milestone'),
    path('milestone/<int:pk>/delete/', views.DeleteMilestoneView.as_view(), name='delete_milestone'),

    # Deliverables
    path('<int:pk>/deliverable/submit/', views.SubmitDeliverableView.as_view(), name='submit_deliverable'),
    path('<int:pk>/deliverable/<int:deliverable_id>/review/', views.ReviewDeliverableView.as_view(),
         name='review_deliverable'),
]

