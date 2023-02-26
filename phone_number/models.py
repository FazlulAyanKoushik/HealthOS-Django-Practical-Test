from django.db import models

from company.models import Company
from customer.models import Customer
from subscription_plan.models import SubscriptionPlan


# Create your models here.
class PhoneNumber(models.Model):
    number = models.CharField(max_length=11, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='phone_numbers')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='phone_numbers')
    subscription = models.ForeignKey(SubscriptionPlan,
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     related_name='phone_numbers')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    otp = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.number)
