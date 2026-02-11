from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Branch, Company, User
from shop.permissions.permissions import HasCompany
from shop.serializers import (
    AuthResponseSerializer,
    BranchCreateSerializer,
    BranchResponseSerializer,
    BranchUpdateSerializer,
    SelectBranchSerializer,
)


@extend_schema(
    tags=["Branches"],
    summary="Get all branches for user's company",
    description="Retrieve all branches belonging to the authenticated user's company.",
    responses={200: BranchResponseSerializer(many=True), 401: None, 403: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, HasCompany])
def get_branches(request):
    user = request.user
    branches = Branch.objects.filter(company=user.company, is_active=True).order_by("-is_main", "name")
    serializer = BranchResponseSerializer(branches, many=True)
    return Response(serializer.data)


@extend_schema(
    tags=["Branches"],
    summary="Get branch by ID",
    description="Retrieve a specific branch by ID.",
    responses={200: BranchResponseSerializer, 404: None, 403: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, HasCompany])
def get_branch(request, branch_id):
    user = request.user
    try:
        branch = Branch.objects.get(id=branch_id, company=user.company)
        serializer = BranchResponseSerializer(branch)
        return Response(serializer.data)
    except Branch.DoesNotExist:
        return Response({"message": "Branch not found"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Branches"],
    summary="Create a new branch",
    description="Create a new branch for the authenticated user's company.",
    request=BranchCreateSerializer,
    responses={201: BranchResponseSerializer, 400: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasCompany])
def create_branch(request):
    user = request.user
    serializer = BranchCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    # Create branch
    branch = Branch.objects.create(
        name=data["name"],
        company=user.company,
        address=data.get("address", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        is_main=data.get("is_main", False),
        created_by=user,
    )

    response_serializer = BranchResponseSerializer(branch)
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Branches"],
    summary="Update branch",
    description="Update an existing branch.",
    request=BranchUpdateSerializer,
    responses={200: BranchResponseSerializer, 404: None, 403: None},
)
@api_view(["PUT"])
@permission_classes([IsAuthenticated, HasCompany])
def update_branch(request, branch_id):
    user = request.user
    try:
        branch = Branch.objects.get(id=branch_id, company=user.company)
    except Branch.DoesNotExist:
        return Response({"message": "Branch not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = BranchUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    for key, value in data.items():
        setattr(branch, key, value)

    branch.save()

    response_serializer = BranchResponseSerializer(branch)
    return Response(response_serializer.data)


@extend_schema(
    tags=["Branches"],
    summary="Delete branch",
    description="Soft delete a branch by setting is_active to False.",
    responses={200: None, 404: None, 403: None},
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated, HasCompany])
def delete_branch(request, branch_id):
    user = request.user
    try:
        branch = Branch.objects.get(id=branch_id, company=user.company)
        branch.is_active = False
        branch.save()
        return Response({"message": "Branch deleted successfully"})
    except Branch.DoesNotExist:
        return Response({"message": "Branch not found"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Branches"],
    summary="Select branch for user",
    description="Set the current branch for the authenticated user.",
    request=SelectBranchSerializer,
    responses={200: AuthResponseSerializer, 404: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated, HasCompany])
def select_branch(request):
    user = request.user
    serializer = SelectBranchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    branch_id = serializer.validated_data["branch_id"]

    try:
        branch = Branch.objects.get(id=branch_id, company=user.company, is_active=True)
        user.branch = branch
        user.save()

        # Return updated user data
        from shop.services import AuthService

        auth_response = AuthService.create_auth_response(user)
        return Response(AuthResponseSerializer(auth_response).data)
    except Branch.DoesNotExist:
        return Response({"message": "Branch not found or inactive"}, status=status.HTTP_404_NOT_FOUND)
