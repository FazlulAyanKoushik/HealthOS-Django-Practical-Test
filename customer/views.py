from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import make_password

from django.contrib.auth import get_user_model, authenticate

from company.models import Company
from customer.models import Customer
from customer.serializers import CustomerSerializer, CustomerSerializerWithToken
from phone_number.models import PhoneNumber

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import random
import stripe

from celery import shared_task
from datetime import timedelta
from django.utils import timezone

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




def ChargeSubscription(phone_number, subscription_plan, stripeToken):

    try:
        if phone_number.is_paid:
            return Response({
                'message': 'Phone number already paid for this month'
            }, status=status.HTTP_400_BAD_REQUEST)

        price = subscription_plan.price

        # Create a new customer in Stripe
        customer = stripe.Customer.create(
            email=phone_number.customer.email,
            source=stripeToken
        )

        phone_number.stripe_customer_id = customer.id
        phone_number.save()

        # Charge the customer using the subscription plan's price
        stripe.Charge.create(
            customer=customer.id,
            # convert the price from its base currency unit to the smallest currency unit
            amount=int(price * 100),
            currency='BDT',
            description=f'Charge for phone number {phone_number.number}'
        )

        phone_number.subscription = subscription_plan
        # Mark the phone number as paid for this month
        phone_number.is_paid = True
        phone_number.save()

        return JsonResponse({
            'message': f'Phone number {phone_number.number} successfully charged'
        })

    except PhoneNumber.DoesNotExist:
        return JsonResponse({
            'message': 'Phone number not found'
        }, status=status.HTTP_404_NOT_FOUND)

    except SubscriptionPlan.DoesNotExist:
        return JsonResponse({
            'message': 'Subscription not found or not active'
        }, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.CardError as e:
        phone_number.is_paid = False
        phone_number.save()
        # Since it's a decline, stripe.error.CardError will be caught
        return JsonResponse({
            'message': 'Card declined'
        }, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        return JsonResponse({
            'message': 'Too many requests made to the API too quickly'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)

    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        return JsonResponse({
            'message': 'Invalid parameters were supplied to Stripe\'s API'
        }, status=status.HTTP_400_BAD_REQUEST)

    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
        return JsonResponse({
            'message': 'Authentication with Stripe\'s API failed'
        }, status=status.HTTP_401_UNAUTHORIZED)

    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        return JsonResponse({
            'message': 'Network communication with Stripe failed'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    except stripe.error.StripeError as e:
        # Something else happened, completely unrelated to Stripe
        return JsonResponse({
            'message': 'Something else happened, completely unrelated to Stripe'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@shared_task(name='check_payment_status')
def check_payment_status():
    # Get all active phone numbers
    phone_numbers = PhoneNumber.objects.filter(is_active=True)

    # Check payment status for each phone number
    for phone_number in phone_numbers:

        if not phone_number.is_paid:

            try:
                stripe.Charge.create(
                    customer=phone_number.stripe_customer_id,
                    # convert the price from its base currency unit to the smallest currency unit
                    amount=int(phone_number.subscription.price * 100),
                    currency='BDT',
                    description=f'Charge for phone number {phone_number.number}'
                )

                phone_number.is_paid = True
                phone_number.save()
            except Exception as e:

                # If subscription plan is unpaid then Company owns the phone number
                phone_number.is_active = False
                phone_number.customer = None
                phone_number.save()

    return f'Checked payment status for {len(phone_numbers)} phone numbers'


def send_phone_number_email(customer, company, number, otp):
    company_name = company.name
    # If there is no phone number for this company,
    if not number:
        email_subject = f'No phone numbers available for {company_name}'
        email_body = f'We are sorry to inform you that there are no phone numbers currently available for {company_name}.Please try again later. You can login now.'

        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_HOST_USER,
            [customer.user.email],
            fail_silently=False,
        )
        return

    # Send the email with the assigned phone number
    email_subject = f'Your phone number for {company_name}'
    email_body = f'Dear valued customer,\n\nWe are pleased to inform you that a unique phone number ({number}) has been assigned to you for your preferred company, {company_name}. Please verify the number using this otp {otp} and keep this number safe as it will be used to identify you when you contact the company.You can login now. \n\nThank you for choosing {company_name}.\n\nSincerely,\nThe {company_name} Team'

    send_mail(
        email_subject,
        email_body,
        settings.EMAIL_HOST_USER,
        [customer.user.email],
        fail_silently=False,
    )