from twilio.rest import Client
from django.conf import settings


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
