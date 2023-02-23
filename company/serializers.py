from rest_framework import serializers

from phone_number.serializers import SecondaryPhoneNumbersSerializer
from subscription_plan.serializers import SecondarySubscriptionsSerializer

from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import Company

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CompanySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    isAdmin = serializers.EmailField(source='user.is_staff', read_only=True)
    company_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'username', 'company_name', 'email', 'isAdmin']

    def get_company_name(self, obj):
        return obj.name


class CompanySerializerWithToken(CompanySerializer):
    id = serializers.SerializerMethodField(source='user.id', read_only=True)
    username = serializers.SerializerMethodField(source='user.username', read_only=True)
    email = serializers.SerializerMethodField(source='user.email', read_only=True)
    isAdmin = serializers.BooleanField(source='user.is_staff', read_only=True)
    access = serializers.SerializerMethodField(read_only=True)
    refresh = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'username', 'email', 'company_name', 'isAdmin', 'access', 'refresh']

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


class CompanySubscriptionSerializer(CompanySerializer):
    subscription_plans = SecondarySubscriptionsSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'username', 'company_name', 'email', 'isAdmin', 'subscription_plans']


class CompanyPhoneNumberSerializer(CompanySerializer):
    phone_numbers = SecondaryPhoneNumbersSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = ['id', 'username', 'company_name', 'email', 'isAdmin', 'phone_numbers']
