from datetime import datetime, timezone

from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Product, Supplier
from shop.serializers import SupplierCreateSerializer, SupplierResponseSerializer


@extend_schema(
    tags=["Suppliers"],
    summary="List all suppliers",
    description="Get all suppliers ordered by last purchase date.",
    responses={200: SupplierResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_suppliers(request):
    company_id = request.user.company_id
    suppliers = Supplier.objects.filter(company_id=company_id).order_by("-last_purchase_date")
    return Response(SupplierResponseSerializer(suppliers, many=True).data)


@extend_schema(
    tags=["Suppliers"],
    summary="Get supplier by ID",
    description="Get a specific supplier's details.",
    responses={200: SupplierResponseSerializer, 404: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_supplier(request, supplier_id):
    company_id = request.user.company_id
    supplier = Supplier.objects.filter(pk=supplier_id, company_id=company_id).first()
    if not supplier:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(SupplierResponseSerializer(supplier).data)


@extend_schema(
    tags=["Suppliers"],
    summary="Create supplier",
    description="Create a new supplier.",
    request=SupplierCreateSerializer,
    responses={201: SupplierResponseSerializer, 401: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_supplier(request):
    user = request.user
    company_id = user.company_id
    if not company_id:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = SupplierCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    supplier = Supplier.objects.create(
        name=data["name"],
        contact_person=data.get("contact_person"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        created_by=user,
        company_id=company_id,
    )
    return Response(SupplierResponseSerializer(supplier).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Suppliers"],
    summary="Update supplier",
    description="Update an existing supplier's information.",
    request=SupplierCreateSerializer,
    responses={200: SupplierResponseSerializer, 404: None},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_supplier(request, supplier_id):
    company_id = request.user.company_id
    supplier = Supplier.objects.filter(pk=supplier_id, company_id=company_id).first()
    if not supplier:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = SupplierCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    supplier.name = data["name"]
    supplier.contact_person = data.get("contact_person")
    supplier.phone = data.get("phone")
    supplier.email = data.get("email")
    supplier.address = data.get("address")
    supplier.save()
    return Response(SupplierResponseSerializer(supplier).data)


@extend_schema(
    tags=["Suppliers"],
    summary="Delete supplier",
    description="Delete a supplier. Cannot delete if they have existing products.",
    responses={204: None, 400: None, 404: None},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_supplier(request, supplier_id):
    company_id = request.user.company_id
    supplier = Supplier.objects.filter(pk=supplier_id, company_id=company_id).first()
    if not supplier:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if Product.objects.filter(supplier_id=supplier_id, is_active=True).exists():
        return Response(
            {"message": "Cannot delete supplier with existing products."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    supplier.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Suppliers"],
    summary="Search suppliers",
    description="Search suppliers by name, contact person, phone, or email.",
    parameters=[OpenApiParameter(name="query", type=str, description="Search query")],
    responses={200: SupplierResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_suppliers(request):
    company_id = request.user.company_id
    query = request.query_params.get("query", "")
    suppliers = Supplier.objects.filter(company_id=company_id).filter(
        Q(name__icontains=query)
        | Q(contact_person__icontains=query)
        | Q(phone__icontains=query)
        | Q(email__icontains=query)
    )
    return Response(SupplierResponseSerializer(suppliers, many=True).data)


@extend_schema(
    tags=["Suppliers"],
    summary="Get top suppliers",
    description="Get suppliers with highest total purchases.",
    parameters=[OpenApiParameter(name="limit", type=int, description="Number of suppliers to return", default=10)],
    responses={200: SupplierResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_top_suppliers(request):
    company_id = request.user.company_id
    limit = int(request.query_params.get("limit", 10))
    suppliers = Supplier.objects.filter(company_id=company_id).order_by("-total_purchases")[:limit]
    return Response(SupplierResponseSerializer(suppliers, many=True).data)
