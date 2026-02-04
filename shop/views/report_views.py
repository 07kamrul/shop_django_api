from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.serializers import (
    DailySalesReportSerializer,
    ProductSalesSerializer,
    ProfitLossReportSerializer,
)
from shop.services import ReportService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profit_loss_report(request):
    company_id = request.user.company_id
    start_date = request.query_params.get("start_date") or request.query_params.get("startDate")
    end_date = request.query_params.get("end_date") or request.query_params.get("endDate")
    try:
        report = ReportService.get_profit_loss_report(company_id, start_date, end_date)
        return Response(ProfitLossReportSerializer(report).data)
    except Exception as e:
        return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_daily_sales_report(request):
    company_id = request.user.company_id
    start_date = request.query_params.get("start_date") or request.query_params.get("startDate")
    end_date = request.query_params.get("end_date") or request.query_params.get("endDate")
    try:
        reports = ReportService.get_daily_sales_report(company_id, start_date, end_date)
        return Response(DailySalesReportSerializer(reports, many=True).data)
    except Exception:
        return Response(
            "An error occurred while generating the report.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_top_products(request):
    company_id = request.user.company_id
    start_date = request.query_params.get("start_date") or request.query_params.get("startDate")
    end_date = request.query_params.get("end_date") or request.query_params.get("endDate")
    limit = int(request.query_params.get("limit", 10))
    try:
        products = ReportService.get_top_selling_products(company_id, start_date, end_date, limit)
        return Response(ProductSalesSerializer(products, many=True).data)
    except Exception:
        return Response(
            "An error occurred while generating the report.",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
