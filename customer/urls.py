from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('register/', views.RegistrationView.as_view(), name="customer-registration"),
    path('login/', views.LoginView.as_view(), name="customer-login"),

    path('number/verify/', views.VerifyPhoneNumber.as_view(), name="customer-verify-number"),
    path('subscription/apply/', views.ApplyPhoneNumberSubscriptionPlan.as_view(), name="customer-subscription-apply"),
]