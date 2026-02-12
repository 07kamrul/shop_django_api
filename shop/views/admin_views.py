from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.permissions.permissions import IsSystemAdmin
from shop.serializers_admin import (
    ApproveCompanySerializer,
    PendingCompanySerializer,
    RejectCompanySerializer,
)
from shop.services.company_service import CompanyService


@extend_schema(
    tags=["Admin"],
    summary="Get pending companies",
    description="System Admin: Get all companies awaiting approval.",
    responses={200: PendingCompanySerializer(many=True), 403: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def get_pending_companies(request):
    companies = CompanyService.get_pending_companies()
    serializer = PendingCompanySerializer(companies, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=["Admin"],
    summary="Approve company",
    description="System Admin: Approve a pending company and activate owner.",
    request=ApproveCompanySerializer,
    responses={200: None, 404: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def approve_company(request):
    serializer = ApproveCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    company_id = serializer.validated_data["company_id"]
    success = CompanyService.approve_company(company_id, request.user, request)

    if success:
        return Response({"message": "Company approved successfully"})
    return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Admin"],
    summary="Reject company",
    description="System Admin: Reject a pending company.",
    request=RejectCompanySerializer,
    responses={200: None, 404: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def reject_company(request):
    serializer = RejectCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    company_id = serializer.validated_data["company_id"]
    reason = serializer.validated_data.get("reason")
    success = CompanyService.reject_company(company_id, request.user, reason, request)

    if success:
        return Response({"message": "Company rejected"})
    return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Admin"],
    summary="Suspend company",
    description="System Admin: Suspend a company and deactivate all users.",
    request=ApproveCompanySerializer,
    responses={200: None, 404: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def suspend_company(request):
    serializer = ApproveCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    company_id = serializer.validated_data["company_id"]
    success = CompanyService.suspend_company(company_id, request.user, request)

    if success:
        return Response({"message": "Company suspended"})
    return Response({"message": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
