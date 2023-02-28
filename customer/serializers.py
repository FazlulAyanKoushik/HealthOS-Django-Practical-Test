from rest_framework import serializers

from customer.models import Customer
from subscription_plan.models import SubscriptionPlan
from subscription_plan.serializers import SubscriptionPlanSerializer, SecondarySubscriptionsSerializer

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from phone_number.serializers import PhoneNumberSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    isAdmin = serializers.EmailField(source='user.is_staff', read_only=True)
    phone_numbers = PhoneNumberSerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'name', 'email', 'isAdmin', 'phone_numbers']


class CustomerSerializerWithToken(CustomerSerializer):
    id = serializers.SerializerMethodField(read_only=True)
    username = serializers.SerializerMethodField(read_only=True)
    email = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.BooleanField(read_only=True)
    access = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'name', 'email', 'isAdmin', 'access', 'refresh']

    def get_access(self, obj):
        token = RefreshToken.for_user(obj.user)
        return str(token.access_token)

    def get_refresh(self, obj):
        token = RefreshToken.for_user(obj.user)
        return str(token)
    def get_id(self, obj):
        return obj.user.id

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_isAdmin(self, obj):
        return obj.user.is_staff

