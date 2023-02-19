from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.http import Http404
from rest_framework import status
from rest_framework.views import APIView

from subscription_plan.models import SubscriptionPlan
from subscription_plan.serializers import SubscriptionPlanSerializer
from company.models import Company


# Create your views here.
class SubscriptionList(APIView):

    def get_object(self, user):
        try:
            company = Company.objects.get(user=user)
            print("found")
            return company
        except Company.DoesNotExist:
            raise Http404('Company does not exist')

    """
        get all subscription plan list by Super User
    """
    permission_classes([IsAdminUser])

    def get(self, request, format=None):

        user = request.user
        if user.is_superuser is True:
            query = SubscriptionPlan.objects.all()
            serializer = SubscriptionPlanSerializer(query, many=True)
            return Response(
                {
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'message': 'User is not a super user'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )


    """
        create subscription by company
    """
    # Require user to have admin role to access this endpoint
    permission_classes([IsAdminUser])

    def post(self, request, format=None):
        # Get the authenticated user making the request
        user = request.user
        # Get the company associated with the authenticated user
        company = self.get_object(user)

        # Extract subscription plan details from the request body
        name = request.data.get('name')
        price = request.data.get('price')
        contract_period = request.data.get('contract_period')

        # Check if the subscription plan already exists for the company
        is_exist = SubscriptionPlan.objects.filter(company=company, name=name).exists()
        if is_exist is True:
            # Return an error response if the plan already exists
            return Response({
                'message': f'Company has already a {name} Subscription plan'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create a new subscription plan instance for the company
        subscription_plan = SubscriptionPlan(
            company=company,
            name=name,
            price=price,
            contract_period=contract_period
        )
        # Set the subscription plan to be active and save it to the database
        subscription_plan.is_active = True
        subscription_plan.save()

        # Serialize the created subscription plan and return a success response
        serializer = SubscriptionPlanSerializer(subscription_plan, many=False)
        return Response(
            {
                'data': serializer.data,
                'message': 'Subscription plan created successfully'
            },
            status=status.HTTP_201_CREATED
        )
