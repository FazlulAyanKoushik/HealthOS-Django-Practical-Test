from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.SubscriptionPlanListView.as_view(), name='get-all-subscription-list'),
    path('add/', views.SubscriptionPlanListView.as_view(), name='add-company-subscription'),
    path('get/<str:pk>/', views.SubscriptionPLanDetailView.as_view(), name='get-company-subscription'),
    path('edit/<str:pk>/', views.SubscriptionPLanDetailView.as_view(), name='edit-company-subscription'),
    path('delete/<str:pk>/', views.SubscriptionPLanDetailView.as_view(), name='delete-company-subscription'),
]