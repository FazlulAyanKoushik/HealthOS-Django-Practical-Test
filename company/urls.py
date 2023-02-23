from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

urlpatterns = [
    # path('login/', views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('register/', views.RegistrationView.as_view(), name='company-registration'),
    path('login/', views.LoginView.as_view(), name='company-login'),

    path('subcription/list/', views.CompanySubscriptionList.as_view(), name='company-subscription-list'),
    path('phonenumber/list/', views.CompanyPhoneNumberList.as_view(), name='company-phonenumber-list'),

    path('list/', views.ALlCompanyList.as_view(), name='all-company-list'),
]