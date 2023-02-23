from rest_framework import serializers
from phone_number.models import PhoneNumber


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = '__all__'


class SecondaryPhoneNumbersSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        exclude = ['company']


class EditPhoneNumbersSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['is_active']
