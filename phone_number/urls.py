from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.PhoneNumberListView.as_view(), name='get-all-phone-numbers'),
    path('add/', views.PhoneNumberListView.as_view(), name='add-phone-number-by-company'),
    path('get/<str:pk>/', views.PhoneNumberDetailView.as_view(), name='get-phone-number-by-company'),
    path('edit/<str:pk>/', views.PhoneNumberDetailView.as_view(), name='edit-phone-number-by-company'),
    path('delete/<str:pk>/', views.PhoneNumberDetailView.as_view(), name='delete-phone-number-by-company'),
]