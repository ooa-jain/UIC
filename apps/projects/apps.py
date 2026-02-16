# apps/projects/apps.py
"""
Purpose: App configuration
Status: Already provided
"""
from django.apps import AppConfig

class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'        # Python path to the app
    label = 'projects'           # short label used by migrations and reverse()
