import secrets
from base64 import b64encode
from datetime import datetime, timedelta, timezone

import bcrypt
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from shop.models import Company, Invitation, User, UserRole
from shop.serializers import (
    AcceptInvitationSerializer,
    CreateInvitationSerializer,
    InvitationResponseSerializer,
)


@extend_schema(
    tags=["Invitations"],
    summary="Test invitations API",
    description="Test endpoint to verify the invitations API is working.",
    responses={200: None},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def invitation_test(request):
    return Response("Invitations API is reaching the controller.")


@extend_schema(
    tags=["Invitations"],
    summary="Create invitation",
    description="Create a new invitation to join a company.",
    request=CreateInvitationSerializer,
    responses={200: InvitationResponseSerializer, 400: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_invitation(request):
    user = request.user
    inviter_role = user.role
    inviter_id = str(user.id)

    serializer = CreateInvitationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    requested_role = int(data["role"])
    company_id = data.get("company_id")

    if inviter_role == UserRole.SYSTEM_ADMIN:
        if requested_role == UserRole.OWNER and not company_id:
            return Response(
                {"message": "CompanyId is required when inviting an Owner."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    elif inviter_role in (UserRole.OWNER, UserRole.MANAGER):
        if requested_role == UserRole.SYSTEM_ADMIN:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if not user.company_id:
            return Response(
                {"message": "Inviter is not associated with a company."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if company_id and company_id != str(user.company_id):
            return Response(
                {"message": "You can only invite users to your own company."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        company_id = str(user.company_id)
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)

    if Invitation.objects.filter(email=data["email"]).exists():
        return Response(
            {"message": f"A user with the email '{data['email']}' already exists in the system."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    token = b64encode(secrets.token_bytes(32)).decode()

    invitation = Invitation.objects.create(
        email=data["email"],
        role=requested_role,
        company_id=company_id,
        invited_by_user_id=inviter_id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    resp = {
        "id": str(invitation.id),
        "email": invitation.email,
        "token": invitation.token,
        "role": invitation.role,
        "company_id": invitation.company_id,
        "expires_at": invitation.expires_at,
    }
    return Response(InvitationResponseSerializer(resp).data)


@extend_schema(
    tags=["Invitations"],
    summary="Accept invitation",
    description="Accept an invitation using token and create a new user account.",
    request=AcceptInvitationSerializer,
    responses={200: None, 400: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def accept_invitation(request):
    serializer = AcceptInvitationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    invitation = Invitation.objects.filter(
        token=data["token"],
        is_accepted=False,
        expires_at__gt=datetime.now(timezone.utc),
    ).first()

    if not invitation:
        return Response("Invalid or expired invitation token.", status=status.HTTP_400_BAD_REQUEST)

    password = data["password"]
    new_user = User(
        name=data["name"],
        email=invitation.email,
        role=invitation.role,
        company_id=invitation.company_id,
        shop_name="N/A",
        is_active=1,
        password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
    )
    new_user.set_password(password)

    if invitation.company_id:
        company = Company.objects.filter(pk=invitation.company_id).first()
        if company:
            new_user.shop_name = company.name

    new_user.save()

    invitation.is_accepted = True
    invitation.save(update_fields=["is_accepted"])

    return Response({
        "message": "Invitation accepted successfully. You can now login.",
        "email": new_user.email,
    })


@extend_schema(
    tags=["Invitations"],
    summary="Claim invitation",
    description="Claim an invitation for an existing logged-in user.",
    responses={200: None, 400: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim_invitation(request):
    token = request.data if isinstance(request.data, str) else request.data.get("token", "")
    user = request.user

    invitation = Invitation.objects.filter(
        token=token,
        is_accepted=False,
        expires_at__gt=datetime.now(timezone.utc),
    ).first()

    if not invitation:
        return Response("Invalid or expired invitation token.", status=status.HTTP_400_BAD_REQUEST)

    if user.company_id:
        return Response("User is already assigned to a company.", status=status.HTTP_400_BAD_REQUEST)

    user.company_id = invitation.company_id
    user.role = invitation.role

    if invitation.company_id:
        company = Company.objects.filter(pk=invitation.company_id).first()
        if company:
            user.shop_name = company.name

    user.save(update_fields=["company_id", "role", "shop_name"])

    invitation.is_accepted = True
    invitation.save(update_fields=["is_accepted"])

    return Response({"message": "Invitation claimed successfully. Features enabled."})


@extend_schema(
    tags=["Invitations"],
    summary="Get my invitations",
    description="Get all pending invitations for the current user's email.",
    responses={200: InvitationResponseSerializer(many=True), 401: None},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_invitations(request):
    user_email = request.user.email
    if not user_email:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    invitations = Invitation.objects.filter(
        email__iexact=user_email,
        is_accepted=False,
        is_rejected=False,
        expires_at__gt=datetime.now(timezone.utc),
    )

    result = []
    for inv in invitations:
        company_name = "Unknown Company"
        if inv.company_id:
            company = Company.objects.filter(pk=inv.company_id).first()
            if company:
                company_name = company.name

        result.append({
            "id": str(inv.id),
            "email": inv.email,
            "role": inv.role,
            "company_id": inv.company_id,
            "company_name": company_name,
            "expires_at": inv.expires_at,
        })

    return Response(result)


@extend_schema(
    tags=["Invitations"],
    summary="Accept invitation by ID",
    description="Accept an invitation by its ID for the logged-in user.",
    responses={200: None, 400: None, 403: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_invitation_by_id(request, invitation_id):
    user = request.user
    user_email = user.email

    invitation = Invitation.objects.filter(pk=invitation_id).first()
    if not invitation:
        return Response("Invitation not found.", status=status.HTTP_400_BAD_REQUEST)

    if invitation.is_accepted or invitation.is_rejected or invitation.expires_at < datetime.now(timezone.utc):
        return Response("Invalid or expired invitation.", status=status.HTTP_400_BAD_REQUEST)

    if invitation.email.lower() != user_email.lower():
        return Response(status=status.HTTP_403_FORBIDDEN)

    if user.company_id:
        return Response("User is already assigned to a company.", status=status.HTTP_400_BAD_REQUEST)

    user.company_id = invitation.company_id
    user.role = invitation.role

    if invitation.company_id:
        company = Company.objects.filter(pk=invitation.company_id).first()
        if company:
            user.shop_name = company.name

    user.save(update_fields=["company_id", "role", "shop_name"])

    invitation.is_accepted = True
    invitation.save(update_fields=["is_accepted"])

    return Response({"message": "Invitation accepted successfully. Features enabled."})


@extend_schema(
    tags=["Invitations"],
    summary="Reject invitation",
    description="Reject an invitation by its ID.",
    responses={200: None, 403: None, 404: None},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_invitation(request, invitation_id):
    user_email = request.user.email

    invitation = Invitation.objects.filter(pk=invitation_id).first()
    if not invitation:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if invitation.email.lower() != user_email.lower():
        return Response(status=status.HTTP_403_FORBIDDEN)

    invitation.is_rejected = True
    invitation.save(update_fields=["is_rejected"])

    return Response({"message": "Invitation rejected."})
