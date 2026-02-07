from datetime import datetime, timezone

from django.db.models import F
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Category, Product, Supplier
from shop.serializers import ProductCreateSerializer, ProductResponseSerializer


def _product_response(product):
    """Ensure category/supplier are loaded for serialization."""
    if not hasattr(product, "_category_loaded"):
        try:
            _ = product.category
        except Exception:
            pass
        try:
            _ = product.supplier
        except Exception:
            pass
    return ProductResponseSerializer(product).data


@extend_schema(
    tags=["Products"],
    summary="List all products",
    description="Get all active products for the authenticated user's company.",
    responses={200: ProductResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products(request):
    company_id = request.user.company_id
    products = (
        Product.objects.filter(company_id=company_id, is_active=True)
        .select_related("category", "supplier")
    )
    return Response(ProductResponseSerializer(products, many=True).data)


@extend_schema(
    tags=["Products"],
    summary="Get product by ID",
    description="Get a specific product by its ID.",
    responses={200: ProductResponseSerializer, 404: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_product(request, product_id):
    company_id = request.user.company_id
    product = (
        Product.objects.select_related("category", "supplier")
        .filter(pk=product_id, company_id=company_id)
        .first()
    )
    if not product:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(ProductResponseSerializer(product).data)


@extend_schema(
    tags=["Products"],
    summary="Create product",
    description="Create a new product in the company's inventory.",
    request=ProductCreateSerializer,
    responses={201: ProductResponseSerializer, 400: None, 401: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_product(request):
    user = request.user
    company_id = user.company_id
    if not company_id:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    serializer = ProductCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    category = Category.objects.filter(pk=data["category_id"], company_id=company_id).first()
    if not category:
        return Response({"message": "Invalid category."}, status=status.HTTP_400_BAD_REQUEST)

    product = Product.objects.create(
        name=data["name"],
        barcode=data.get("barcode"),
        category=category,
        buying_price=data["buying_price"],
        selling_price=data["selling_price"],
        current_stock=data["current_stock"],
        min_stock_level=data.get("min_stock_level", 10),
        supplier_id=data.get("supplier_id"),
        created_by=user,
        company_id=company_id,
    )

    product = Product.objects.select_related("category", "supplier").get(pk=product.pk)
    return Response(
        ProductResponseSerializer(product).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    tags=["Products"],
    summary="Update product",
    description="Update an existing product's information.",
    request=ProductCreateSerializer,
    responses={200: ProductResponseSerializer, 400: None, 404: None},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_product(request, product_id):
    company_id = request.user.company_id
    product = Product.objects.filter(pk=product_id, company_id=company_id).first()
    if not product:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = ProductCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    category = Category.objects.filter(pk=data["category_id"], company_id=company_id).first()
    if not category:
        return Response({"message": "Invalid category."}, status=status.HTTP_400_BAD_REQUEST)

    product.name = data["name"]
    product.barcode = data.get("barcode")
    product.category = category
    product.buying_price = data["buying_price"]
    product.selling_price = data["selling_price"]
    product.current_stock = data["current_stock"]
    product.min_stock_level = data.get("min_stock_level", 10)
    product.supplier_id = data.get("supplier_id")
    product.save()

    product = Product.objects.select_related("category", "supplier").get(pk=product.pk)
    return Response(ProductResponseSerializer(product).data)


@extend_schema(
    tags=["Products"],
    summary="Delete product",
    description="Soft delete a product (marks as inactive).",
    responses={204: None, 404: None},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_product(request, product_id):
    company_id = request.user.company_id
    product = Product.objects.filter(pk=product_id, company_id=company_id).first()
    if not product:
        return Response(status=status.HTTP_404_NOT_FOUND)

    product.is_active = False
    product.save(update_fields=["is_active"])
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=["Products"],
    summary="Get low stock products",
    description="Get products with stock at or below minimum level.",
    responses={200: ProductResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_low_stock_products(request):
    company_id = request.user.company_id
    products = (
        Product.objects.filter(
            company_id=company_id,
            is_active=True,
            current_stock__lte=F("min_stock_level"),
        )
        .select_related("category", "supplier")
    )
    return Response(ProductResponseSerializer(products, many=True).data)
