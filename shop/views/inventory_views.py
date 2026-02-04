from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.serializers import (
    CategoryInventorySerializer,
    InventorySummarySerializer,
    ProductResponseSerializer,
    StockAlertSerializer,
)
from shop.services import InventoryService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_inventory_summary(request):
    company_id = request.user.company_id
    summary = InventoryService.get_inventory_summary(company_id)
    return Response(InventorySummarySerializer(summary).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_stock_alerts(request):
    company_id = request.user.company_id
    alerts = InventoryService.get_stock_alerts(company_id)
    return Response(StockAlertSerializer(alerts, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_category_inventory(request):
    company_id = request.user.company_id
    data = InventoryService.get_category_inventory(company_id)
    return Response(CategoryInventorySerializer(data, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_products_needing_restock(request):
    company_id = request.user.company_id
    products = InventoryService.get_products_needing_restock(company_id)
    return Response(ProductResponseSerializer(products, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_inventory_turnover(request):
    company_id = request.user.company_id
    start_date = request.query_params.get("start_date") or request.query_params.get("startDate")
    end_date = request.query_params.get("end_date") or request.query_params.get("endDate")
    if not start_date or not end_date:
        return Response(
            {"message": "start_date and end_date are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    turnover = InventoryService.calculate_inventory_turnover(company_id, start_date, end_date)
    return Response(turnover)
