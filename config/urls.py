# config/urls.py
#Root URL routing
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # App URLs
    path('accounts/', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    #path('messages/', include('apps.messaging.urls')),
    #path('payments/', include('apps.payments.urls')),
    #path('reviews/', include('apps.reviews.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
