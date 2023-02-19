from rest_framework import serializers
from subscription_plan.models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class SecondarySubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        # fields = ['id', 'name', 'price', 'contract_period', 'is_active']
        exclude = ['company']
