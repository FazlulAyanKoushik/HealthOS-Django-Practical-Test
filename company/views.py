from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import make_password

from company.models import Company
from company.serializers import CompanySerializer, CompanySerializerWithToken, UserSerializer, \
    CompanySubscriptionSerializer
from django.contrib.auth import get_user_model, authenticate

from subscription_plan.models import SubscriptionPlan
from subscription_plan.serializers import SubscriptionPlanSerializer

User = get_user_model()


# Create your views here.
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # refresh = self.get_token(self.user)
        serializer = CompanySerializerWithToken(self.user).data

        for k, v in serializer.items():
            data[k] = v
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


"""
    company registration view
"""


class RegistrationView(APIView):

    def post(self, request, format=None):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        company_name = request.data.get('company_name')

        # Check if the username, email, password and company_name fields are present in the request data
        if username is None:
            return Response({'error': 'Please provide a username'}, status=status.HTTP_400_BAD_REQUEST)

        if email is None:
            return Response({'error': 'Please provide a email'}, status=status.HTTP_400_BAD_REQUEST)

        if password is None:
            return Response({'error': 'Please provide  password'}, status=status.HTTP_400_BAD_REQUEST)

        if company_name is None:
            return Response({'error': 'Please provide a company name'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the username is already taken
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username is already taken'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if the email is already taken
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email is already registered'}, status=status.HTTP_400_BAD_REQUEST)

        if Company.objects.filter(name=company_name).exists():
            return Response({'error': 'Company with this name is already registered'},
                            status=status.HTTP_400_BAD_REQUEST
                            )

        user = User(username=username, email=email)
        user.set_password(password)
        user.is_staff = True
        user.save()

        company = Company.objects.create(user=user, name=company_name)

        serializer = CompanySerializer(company, many=False)

        return Response(
            {
                'data': serializer.data,
                'message': 'Company created successfully'
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
        company = Company.objects.get(user=user)

        # Serialize the company data with a JWT token
        serializer = CompanySerializerWithToken(company)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get(self, request):
        q = User.objects.all()
        userSerializer = UserSerializer(q, many=True)
        t = Company.objects.all()
        companySerializer = CompanySerializer(t, many=True)
        return Response(
            {
                'user_data': userSerializer.data,
                'company_data': companySerializer.data
            }
        )


class CompanySubscriptionList(APIView):
    def get_object(self, user):
        try:
            company = Company.objects.get(user=user)
            print("found")
            return company
        except Company.DoesNotExist:
            raise Http404('Company does not exist')


    permission_classes([IsAdminUser])
    def get(self, request, format=None):
        company = self.get_object(request.user)
        serializer = CompanySubscriptionSerializer(company)
        return Response(
            {
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
