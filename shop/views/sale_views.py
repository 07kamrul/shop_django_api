from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.serializers import (
    SaleCreateSerializer,
    SaleResponseSerializer,
    SaleUpdateSerializer,
)
from shop.services import SaleService


@extend_schema(
    tags=["Sales"],
    summary="List all sales",
    description="Get all sales with optional date filtering.",
    parameters=[
        OpenApiParameter(name="start_date", type=str, description="Start date filter (YYYY-MM-DD)"),
        OpenApiParameter(name="end_date", type=str, description="End date filter (YYYY-MM-DD)"),
    ],
    responses={200: SaleResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sales(request):
    company_id = request.user.company_id
    start_date = request.query_params.get("start_date") or request.query_params.get("startDate")
    end_date = request.query_params.get("end_date") or request.query_params.get("endDate")
    sales = SaleService.get_sales(company_id, start_date=start_date, end_date=end_date)
    return Response(SaleResponseSerializer(sales, many=True).data)


@extend_schema(
    tags=["Sales"],
    summary="Get sale by ID",
    description="Get a specific sale with its items.",
    responses={200: SaleResponseSerializer, 404: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_sale(request, sale_id):
    company_id = request.user.company_id
    sale = SaleService.get_sale_by_id(sale_id, company_id)
    if not sale:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(SaleResponseSerializer(sale).data)


@extend_schema(
    tags=["Sales"],
    summary="Create sale",
    description="Create a new sale with items. Automatically updates product stock.",
    request=SaleCreateSerializer,
    responses={201: SaleResponseSerializer, 400: None, 401: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sale(request):
    serializer = SaleCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        sale = SaleService.create_sale(serializer.validated_data, request.user)
        sale_data = SaleService.get_sale_by_id(str(sale.id), request.user.company_id)
        return Response(SaleResponseSerializer(sale_data).data, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return Response(
            {"message": "An error occurred while creating the sale."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Sales"],
    summary="Update sale",
    description="Update an existing sale and its items.",
    request=SaleUpdateSerializer,
    responses={200: SaleResponseSerializer, 400: None, 404: None},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_sale(request, sale_id):
    serializer = SaleUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        sale = SaleService.update_sale(sale_id, serializer.validated_data, request.user)
        if not sale:
            return Response(status=status.HTTP_404_NOT_FOUND)
        sale_data = SaleService.get_sale_by_id(str(sale.id), request.user.company_id)
        return Response(SaleResponseSerializer(sale_data).data)
    except ValueError as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    except Exception:
        return Response(
            {"message": "An error occurred while updating the sale."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Sales"],
    summary="Delete sale",
    description="Delete a sale and restore product stock.",
    responses={204: None, 401: None, 404: None},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_sale(request, sale_id):
    try:
        result = SaleService.delete_sale(sale_id, request.user)
        if not result:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except PermissionError:
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    tags=["Sales"],
    summary="Get today's sales",
    description="Get all sales from today.",
    responses={200: SaleResponseSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_today_sales(request):
    company_id = request.user.company_id
    sales = SaleService.get_today_sales(company_id)
    return Response(SaleResponseSerializer(sales, many=True).data)
