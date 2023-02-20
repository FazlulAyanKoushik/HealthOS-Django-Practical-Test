
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/company/', include('company.urls')),
    path('api/subscription/', include('subscription_plan.urls')),
    path('api/phone_number/', include('phone_number.urls'))
]
