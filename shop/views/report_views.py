from drf_spectacular.utils import extend_schema, OpenApiParameter
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


@extend_schema(
    tags=["Reports"],
    summary="Get profit/loss report",
    description="Get profit and loss report for a date range.",
    parameters=[
        OpenApiParameter(name="start_date", type=str, description="Start date (YYYY-MM-DD)"),
        OpenApiParameter(name="end_date", type=str, description="End date (YYYY-MM-DD)"),
    ],
    responses={200: ProfitLossReportSerializer},
)
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


@extend_schema(
    tags=["Reports"],
    summary="Get daily sales report",
    description="Get daily sales breakdown for a date range.",
    parameters=[
        OpenApiParameter(name="start_date", type=str, description="Start date (YYYY-MM-DD)"),
        OpenApiParameter(name="end_date", type=str, description="End date (YYYY-MM-DD)"),
    ],
    responses={200: DailySalesReportSerializer(many=True)},
)
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


@extend_schema(
    tags=["Reports"],
    summary="Get top selling products",
    description="Get top selling products for a date range.",
    parameters=[
        OpenApiParameter(name="start_date", type=str, description="Start date (YYYY-MM-DD)"),
        OpenApiParameter(name="end_date", type=str, description="End date (YYYY-MM-DD)"),
        OpenApiParameter(name="limit", type=int, description="Number of products to return", default=10),
    ],
    responses={200: ProductSalesSerializer(many=True)},
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
