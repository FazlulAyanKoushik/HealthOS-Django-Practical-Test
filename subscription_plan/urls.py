from django.urls import path
from . import views


urlpatterns = [
    path('list/', views.SubscriptionList.as_view(), name='get-company-subscription-list'),
    path('add/', views.SubscriptionList.as_view(), name='add-company-subscription')
]