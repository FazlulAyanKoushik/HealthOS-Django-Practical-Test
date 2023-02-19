from django.db import models

from company.models import Company


# Create your models here.
class SubscriptionPlan(models.Model):
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'
    NAME_CHOICES = [
        (BRONZE, 'Globalnet Bronze - 500 BDT / month, 12 months'),
        (SILVER, 'Globalnet Silver - 750 BDT / month, 12 months'),
        (GOLD, 'Globalnet Gold - 1500 BDT / month, no contract'),
    ]
    name = models.CharField(choices=NAME_CHOICES, max_length=10)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscription_plans')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    contract_period = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.company.name} - {self.name} - {self.price} BDT/month, {self.contract_period} months'
