from datetime import datetime, timezone

from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Customer, Sale
from shop.serializers import CustomerCreateSerializer, CustomerResponseSerializer


@extend_schema(
    tags=["Customers"],
    summary="List all customers",
    description="Get all customers ordered by last purchase date.",
    responses={200: CustomerResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customers(request):
    company_id = request.user.company_id
    customers = Customer.objects.filter(company_id=company_id).order_by("-last_purchase_date")
    return Response(CustomerResponseSerializer(customers, many=True).data)


@extend_schema(
    tags=["Customers"],
    summary="Get customer by ID",
    description="Get a specific customer's details.",
    responses={200: CustomerResponseSerializer, 404: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customer(request, customer_id):
    company_id = request.user.company_id
    customer = Customer.objects.filter(pk=customer_id, company_id=company_id).first()
    if not customer:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(CustomerResponseSerializer(customer).data)


@extend_schema(
    tags=["Customers"],
    summary="Create customer",
    description="Create a new customer.",
    request=CustomerCreateSerializer,
    responses={201: CustomerResponseSerializer, 401: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_customer(request):
    user = request.user
    company_id = user.company_id
    if not company_id:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = CustomerCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    customer = Customer.objects.create(
        name=data["name"],
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        created_by=user,
        company_id=company_id,
    )
    return Response(CustomerResponseSerializer(customer).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Customers"],
    summary="Update customer",
    description="Update an existing customer's information.",
    request=CustomerCreateSerializer,
    responses={200: CustomerResponseSerializer, 404: None},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_customer(request, customer_id):
    company_id = request.user.company_id
    customer = Customer.objects.filter(pk=customer_id, company_id=company_id).first()
    if not customer:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = CustomerCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    customer.name = data["name"]
    customer.phone = data.get("phone")
    customer.email = data.get("email")
    customer.address = data.get("address")
    customer.save()
    return Response(CustomerResponseSerializer(customer).data)


@extend_schema(
    tags=["Customers"],
    summary="Delete customer",
    description="Delete a customer. Cannot delete if they have existing sales.",
    responses={204: None, 400: None, 404: None},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_customer(request, customer_id):
    company_id = request.user.company_id
    customer = Customer.objects.filter(pk=customer_id, company_id=company_id).first()
    if not customer:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if Sale.objects.filter(customer_id=customer_id).exists():
        return Response(
            {"message": "Cannot delete customer with existing sales."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Customers"],
    summary="Search customers",
    description="Search customers by name, phone, or email.",
    parameters=[OpenApiParameter(name="query", type=str, description="Search query")],
    responses={200: CustomerResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_customers(request):
    company_id = request.user.company_id
    query = request.query_params.get("query", "")
    customers = Customer.objects.filter(
        company_id=company_id,
    ).filter(
        Q(name__icontains=query) | Q(phone__icontains=query) | Q(email__icontains=query)
    )
    return Response(CustomerResponseSerializer(customers, many=True).data)


@extend_schema(
    tags=["Customers"],
    summary="Get top customers",
    description="Get customers with highest total purchases.",
    parameters=[OpenApiParameter(name="limit", type=int, description="Number of customers to return", default=10)],
    responses={200: CustomerResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_top_customers(request):
    company_id = request.user.company_id
    limit = int(request.query_params.get("limit", 10))
    customers = Customer.objects.filter(company_id=company_id).order_by("-total_purchases")[:limit]
    return Response(CustomerResponseSerializer(customers, many=True).data)
