
# apps/messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.ConversationListView.as_view(), name='inbox'),
    path('<int:pk>/', views.ConversationDetailView.as_view(), name='conversation'),
    path('send/', views.SendMessageView.as_view(), name='send'),
]