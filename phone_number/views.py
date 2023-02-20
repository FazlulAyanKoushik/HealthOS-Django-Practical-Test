from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView

from phone_number.models import PhoneNumber
from phone_number.serializers import PhoneNumberSerializer, SecondaryPhoneNumbersSerializer
from company.models import Company



permission_classes([IsAdminUser])
class PhoneNumberListView(APIView):
    def get_object(self, user):
        try:
            company = Company.objects.get(user=user)
            print("found")
            return company
        except Company.DoesNotExist:
            raise Http404('Company does not exist')

    """
        GET method to retrieve all phone numbers. Only accessible by Super admin users.
    """

    def get(self, request, format=None):
        user = request.user
        # Check if user is a superuser
        if user.is_superUser is True:
            # Retrieve all SubscriptionPlan objects from the database
            query = PhoneNumber.objects.all()
            # Serialize the data
            serializer = PhoneNumberSerializer(query, many=True)
            return Response(
                {
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:  # If user is not a superuser, return unauthorized status
            return Response(
                {
                    'message': 'User is not a super user'
                }, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        user = request.user
        # Get the company associated with the authenticated user
        company = self.get_object(user)

        # request body
        number = request.data.get('phone_number')

        # Check if the phone number already exists
        is_exist = PhoneNumber.objects.filter(number=number).exists()
        if is_exist is True:
            # Return an error response if the number already exists
            return Response({
                'message': f'Already exist This number : {number}'
            })

        # Create a new phone number instance for the company
        phone_number = PhoneNumber(
            number=number,
            company=company
        )
        phone_number.save()
        # Serialize the created phone number and return a success response
        serializer = PhoneNumberSerializer(phone_number, many=False)
        return Response(
            {
                'data': serializer.data,
                'message': 'Phone number created successfully'
            },
            status=status.HTTP_201_CREATED
        )


permission_classes([IsAdminUser])
class PhoneNumberDetailView(APIView):
    # Retrieve a Company object based on the user.
    def get_object(self, user):
        try:
            company = Company.objects.get(user=user)
            return company
        except Company.DoesNotExist:
            raise Http404('Company does not exist')

    def get_phone_number(self, pk):
        try:
            phone_number = PhoneNumber.objects.get(number=pk)
            return phone_number
        except PhoneNumber.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        # Get the company associated with the authenticated user
        company = self.get_object(request.user)

        phone_number = self.get_phone_number(pk)
        if phone_number.company == company:
            serializer = PhoneNumberSerializer(phone_number, many=False)
            return Response(
                {
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    'message': 'Not valid user'
                }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        # Get the company associated with the authenticated user
        company = self.get_object(request.user)

        is_active = request.data.get('is_active')
        phone_number = self.get_phone_number(pk)

        if phone_number.company == company:
            serializer = SecondaryPhoneNumbersSerializer(phone_number, data=request.data)
            if serializer.is_valid():
                serializer.save()
                serializer = PhoneNumberSerializer(phone_number, many=False)
                return Response(serializer.data, status=status.HTTP_200_OK)

        return Response({
            'message': 'Not valid user'
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        # Get the company associated with the authenticated user
        company = self.get_object(request.user)
        phone_number = self.get_phone_number(pk)

        if phone_number.company == company:
            phone_number.delete()
            return Response({
                'message': 'Deleted successfully'
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Not valid user'
        }, status=status.HTTP_400_BAD_REQUEST)


