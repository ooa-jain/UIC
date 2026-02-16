
# apps/payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.PaymentListView.as_view(), name='list'),
    path('create/<int:project_id>/', views.CreatePaymentView.as_view(), name='create'),
    path('<int:pk>/release/', views.ReleasePaymentView.as_view(), name='release'),
]
