
# apps/reviews/urls.py
from django.urls import path
from apps.reviews.urls import views

app_name = 'reviews'

urlpatterns = [
    path('create/<int:project_id>/', views.CreateReviewView.as_view(), name='create'),
    path('my-reviews/', views.MyReviewsView.as_view(), name='my_reviews'),
]