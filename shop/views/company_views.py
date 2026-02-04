from datetime import datetime, timezone

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shop.models import Company, User, UserRole
from shop.permissions import IsOwner, IsSystemAdmin
from shop.serializers import (
    CompanyResponseSerializer,
    CompanyUpdateSerializer,
    CompanyUserResponseSerializer,
    CreateCompanySerializer,
    InviteUserSerializer,
    LinkUserToCompanySerializer,
    UpdateUserRoleSerializer,
)
from shop.services import AuthService


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_company(request):
    company_id = request.user.company_id
    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)
    company = Company.objects.filter(pk=company_id).first()
    if not company:
        return Response({"message": "Company not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(CompanyResponseSerializer(company).data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsOwner])
def update_company(request):
    company_id = request.user.company_id
    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)
    company = Company.objects.filter(pk=company_id).first()
    if not company:
        return Response({"message": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = CompanyUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    for field in ["name", "description", "phone", "email", "address", "logo_url", "currency", "timezone"]:
        if field in data and data[field] is not None:
            setattr(company, field, data[field])

    company.updated_at = datetime.now(timezone.utc)
    company.save()
    return Response(CompanyResponseSerializer(company).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_users(request):
    user = request.user
    if user.role == UserRole.SYSTEM_ADMIN:
        users = User.objects.all()
    else:
        if not user.company_id:
            return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)
        if user.role not in (UserRole.OWNER, UserRole.MANAGER):
            return Response(status=status.HTTP_403_FORBIDDEN)
        users = User.objects.filter(company_id=user.company_id)

    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "shop_name": u.shop_name,
            "phone": u.phone,
            "role": u.role,
            "created_at": u.created_at,
            "last_login_at": u.last_login_at,
            "is_active": u.is_active == 1,
        }
        for u in users
    ]
    return Response(CompanyUserResponseSerializer(data, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_users(request):
    query = request.query_params.get("query", "")
    if not query:
        return Response([])

    users = User.objects.filter(
        Q(email__icontains=query) | Q(name__icontains=query)
    )[:10]

    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "shop_name": u.shop_name,
            "phone": u.phone,
            "role": u.role,
            "created_at": u.created_at,
            "last_login_at": u.last_login_at,
            "is_active": u.is_active == 1,
        }
        for u in users
    ]
    return Response(CompanyUserResponseSerializer(data, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOwner])
def invite_user(request):
    company_id = request.user.company_id
    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = InviteUserSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if int(data["role"]) == UserRole.OWNER:
        return Response(
            {"message": "Cannot invite another Owner. Each company can have only one Owner."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = AuthService.invite_user(data, str(company_id))
        resp = {
            "id": result["id"],
            "email": result["email"],
            "name": result["name"],
            "phone": result["phone"],
            "role": result["role"],
            "created_at": datetime.now(timezone.utc),
            "last_login_at": None,
            "is_active": True,
            "shop_name": None,
        }
        return Response(CompanyUserResponseSerializer(resp).data)
    except ValueError as e:
        return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsOwner])
def update_user_role(request, user_id):
    company_id = request.user.company_id
    current_user_id = str(request.user.id)

    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)

    if user_id == current_user_id:
        return Response({"message": "Cannot change your own role."}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UpdateUserRoleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    new_role = int(serializer.validated_data["role"])

    if new_role == UserRole.OWNER:
        return Response(
            {"message": "Cannot promote user to Owner."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(pk=user_id, company_id=company_id).first()
    if not user:
        return Response({"message": "User not found in your company."}, status=status.HTTP_404_NOT_FOUND)

    if user.role == UserRole.OWNER:
        return Response({"message": "Cannot change the Owner's role."}, status=status.HTTP_400_BAD_REQUEST)

    user.role = new_role
    user.save(update_fields=["role"])
    return Response({"message": "User role updated successfully."})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsOwner])
def remove_user(request, user_id):
    company_id = request.user.company_id
    current_user_id = str(request.user.id)

    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)
    if user_id == current_user_id:
        return Response({"message": "Cannot remove yourself from the company."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(pk=user_id, company_id=company_id).first()
    if not user:
        return Response({"message": "User not found in your company."}, status=status.HTTP_404_NOT_FOUND)
    if user.role == UserRole.OWNER:
        return Response({"message": "Cannot remove the company Owner."}, status=status.HTTP_400_BAD_REQUEST)

    user.is_active = 0
    user.company = None
    user.save(update_fields=["is_active", "company"])
    return Response({"message": "User removed from company successfully."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsOwner])
def activate_user(request, user_id):
    company_id = request.user.company_id
    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)

    user = User.objects.filter(pk=user_id, company_id=company_id).first()
    if not user:
        return Response({"message": "User not found in your company."}, status=status.HTTP_404_NOT_FOUND)

    user.is_active = 1
    user.save(update_fields=["is_active"])
    return Response({"message": "User activated successfully."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated, IsOwner])
def deactivate_user(request, user_id):
    company_id = request.user.company_id
    current_user_id = str(request.user.id)

    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)
    if user_id == current_user_id:
        return Response({"message": "Cannot deactivate yourself."}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.filter(pk=user_id, company_id=company_id).first()
    if not user:
        return Response({"message": "User not found in your company."}, status=status.HTTP_404_NOT_FOUND)
    if user.role == UserRole.OWNER:
        return Response({"message": "Cannot deactivate the company Owner."}, status=status.HTTP_400_BAD_REQUEST)

    user.is_active = 0
    user.save(update_fields=["is_active"])
    return Response({"message": "User deactivated successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsOwner])
def get_pending_users(request):
    users = User.objects.filter(Q(company__isnull=True) | Q(company_id=""))

    data = [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "phone": u.phone,
            "role": u.role,
            "created_at": u.created_at,
            "last_login_at": u.last_login_at,
            "is_active": u.is_active == 1,
            "shop_name": None,
        }
        for u in users
    ]
    return Response(CompanyUserResponseSerializer(data, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsOwner])
def link_user_to_company(request):
    company_id = request.user.company_id
    if not company_id:
        return Response({"message": "No company context found."}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = LinkUserToCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if int(data["role"]) == UserRole.OWNER:
        return Response(
            {"message": "Cannot assign Owner role."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.filter(pk=data["user_id"]).first()
    if not user:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    if user.company_id:
        return Response(
            {"message": "User is already linked to a company."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    company = Company.objects.filter(pk=company_id).first()
    if not company:
        return Response({"message": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

    user.company = company
    user.role = int(data["role"])
    user.is_active = 1
    user.shop_name = company.name
    user.save(update_fields=["company", "role", "is_active", "shop_name"])

    resp = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
        "is_active": True,
        "shop_name": user.shop_name,
    }
    return Response(CompanyUserResponseSerializer(resp).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def create_company(request):
    serializer = CreateCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    company = Company.objects.create(
        name=data["name"],
        description=data.get("description", ""),
        address=data.get("address", ""),
        phone=data.get("phone", ""),
        email=data.get("email", ""),
        currency=data.get("currency", "BDT"),
        timezone=data.get("timezone", "Asia/Dhaka"),
        owner=request.user,
    )
    return Response(CompanyResponseSerializer(company).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def assign_user_to_company(request, company_id):
    company = Company.objects.filter(pk=company_id).first()
    if not company:
        return Response({"message": "Company not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = LinkUserToCompanySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    user = User.objects.filter(pk=data["user_id"]).first()
    if not user:
        return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if user.company_id and str(user.company_id) != company_id:
        return Response(
            {"message": f"User is already linked to another company ({user.company_id})."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.company = company
    user.role = int(data["role"])
    user.is_active = 1
    user.shop_name = company.name
    user.save(update_fields=["company", "role", "is_active", "shop_name"])

    if int(data["role"]) == UserRole.OWNER:
        company.owner = user
        company.save(update_fields=["owner"])

    return Response({"message": "User assigned to company successfully."})


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsSystemAdmin])
def get_all_companies(request):
    companies = Company.objects.all()
    return Response(CompanyResponseSerializer(companies, many=True).data)
