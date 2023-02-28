
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework import status
from rest_framework.views import APIView


from django.contrib.auth import get_user_model, authenticate

from company.models import Company
from customer.models import Customer
from customer.serializers import CustomerSerializer, CustomerSerializerWithToken
from phone_number.models import PhoneNumber
from customer.utilities import send_otp, send_phone_number_email, ChargeSubscription

from django.conf import settings
import random
import stripe

from celery import shared_task

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
class RegistrationView(APIView):

    def post(self, request, format=None):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        customer_name = request.data.get('name')
        company_name = request.data.get('company_name')

        # Check if the username, email, password and company_name fields are present in the request data
        if username is None:
            return Response({'error': 'Please provide a username'}, status=status.HTTP_400_BAD_REQUEST)

        if email is None:
            return Response({'error': 'Please provide a email'}, status=status.HTTP_400_BAD_REQUEST)

        if password is None:
            return Response({'error': 'Please provide  password'}, status=status.HTTP_400_BAD_REQUEST)

        if customer_name is None:
            return Response({'error': 'Please provide a name'}, status=status.HTTP_400_BAD_REQUEST)

        if company_name is None:
            return Response({'error': 'Please provide a company name'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the username is already taken
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username is already taken'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if the email is already taken
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email is already registered'}, status=status.HTTP_400_BAD_REQUEST)

        if Customer.objects.filter(name=customer_name).exists():
            return Response({'error': 'Company with this name is already registered'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        user = User(username=username, email=email)
        user.set_password(password)
        user.save()


        customer = Customer.objects.create(user=user, name=customer_name)
        serializer = CustomerSerializer(customer, many=False)

        company = Company.objects.get(name=company_name)
        phone_number = PhoneNumber.objects.filter(
            customer=None, company=company).order_by('?').first()

        otp = None

        if phone_number:
            otp = str(random.randint(1000, 9999))
            phone_number.customer = customer
            phone_number.otp = otp
            phone_number.save()

        has_primary_number = PhoneNumber.objects.filter(customer=customer, is_primary=True).exists()

        if not has_primary_number:
            phone_number.is_primary = True
            phone_number.save()

        send_phone_number_email(customer, company, phone_number, otp)

        return Response(
            {
                'data': serializer.data,
                'message': 'User created successfully'
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    def post(self, request, format=None):
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if the username and password fields are present in the request data
        if username is None or password is None:
            return Response({'error': 'Please provide a username and password'}, status=status.HTTP_400_BAD_REQUEST)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the associated company
        customer = Customer.objects.get(user=user)

        # Serialize the company data with a JWT token
        serializer = CustomerSerializerWithToken(customer, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


permission_classes([IsAuthenticated])
class VerifyPhoneNumber(APIView):
    def post(self, request, format=None):
        phone_number = request.data.get("phone_number")
        otp = request.data.get("otp")

        if phone_number is None or otp is None:
            return Response({
                'message': 'Required Field missing'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                phone_number = PhoneNumber.objects.get(number=phone_number)
                if phone_number is None:
                    return Response({
                        'message': 'Phone number not exist'
                    }, status=status.HTTP_400_BAD_REQUEST)

                if phone_number.otp == otp:
                    phone_number.is_active = True
                    phone_number.save()
                    return Response({
                        'message': 'Phone number verified and activated'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': 'otp not matched'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'message': 'Phone number does not exist.'
                }, status=status.HTTP_400_BAD_REQUEST)


permission_classes([IsAuthenticated])
class ApplyPhoneNumberSubscriptionPlan(APIView):
    def get_object(self, phone_number):
        try:
            phone_number = PhoneNumber.objects.get(number=phone_number)
            return phone_number
        except Exception as e:
            return Response({
                'message': 'Phone number not exist'
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, format=None):
        phone_number = request.data.get("phone_number")
        subscription_name = request.data.get("name")
        stripeToken = request.data['stripeToken']

        phone_number = self.get_object(phone_number)

        try:
            subscription_plan = SubscriptionPlan.objects.get(
                company=phone_number.company, is_active=True,
                name=subscription_name)

            ChargeSubscription(phone_number, subscription_plan, stripeToken)
        except:
            return Response({
                'message': 'Subscription not found or not active'
            }, status=status.HTTP_400_BAD_REQUEST)


permission_classes([IsAdminUser])
class GetCustomerView(APIView):
    def get_object(self, user):
        try:
            company = Company.objects.get(user=user)
            return company
        except Company.DoesNotExist:
            raise Http404('Company does not exist')
    def get(self, request, format=None):
        company = self.get_object(request.user)
        phone_number = request.data.get('phone_number')

        try:
            phone_number = PhoneNumber.objects.get(company=company, number=phone_number)
        except:
            return Response(
                {
                    'message': 'Phone number not exists'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if phone_number.customer is None:
            return Response(
                {
                    'message': 'There is no customer available'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        customer_phone_numbers = phone_number.customer.phone_numbers.filter(company=company)
        serializer = PhoneNumberSerializer(customer_phone_numbers)

        return Response({
            'id': phone_number.customer.user.id,
            'email': phone_number.customer.user.email,
            'name': phone_number.customer.name,
            'phone_numbers': serializer.data
        }, status=status.HTTP_200_OK)
