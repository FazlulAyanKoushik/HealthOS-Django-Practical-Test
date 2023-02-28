from django.http import JsonResponse
from rest_framework import status
from twilio.rest import Client
from django.conf import settings
from rest_framework.response import Response

from django.conf import settings
import random
import stripe

from celery import shared_task

from phone_number.models import PhoneNumber
from subscription_plan.models import SubscriptionPlan

stripe.api_key = settings.STRIPE_SECRET_KEY

from django.core.mail import send_mail


def send_otp(phone_number, otp):
    # Twilio client with  account SID and auth token
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    # Check if the phone number starts with 0 and modify it accordingly
    if phone_number.startswith('0'):
        phone_number = '+88' + phone_number
    else:
        phone_number = '+880' + phone_number
    # Twilio API to send an SMS message with the OTP to the specified phone number
    message = client.messages.create(
        to=phone_number,
        from_=settings.TWILIO_PHONE_NUMBER,
        body="Your OTP is: " + otp
    )


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
