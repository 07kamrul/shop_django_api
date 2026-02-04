import secrets
import string
from datetime import datetime, timedelta, timezone

import bcrypt
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

from shop.models import Company, User, UserRole


class AuthService:

    @staticmethod
    def simple_register(data):
        email = data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValueError("User with this email already exists.")

        password = data["password"]
        user = User(
            email=email,
            name=data["name"],
            shop_name="Pending",
            phone=data.get("phone"),
            password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            role=UserRole.UNASSIGNED_USER,
            company=None,
            is_active=1,
        )
        user.set_password(password)
        user.save()

        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "message": "Registration successful. You can now login to your dashboard.",
        }

    @staticmethod
    def login(data):
        email = data["email"].strip().lower()
        password = data["password"]

        if not email or not password:
            raise ValueError("Email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise PermissionError("Invalid email or password.")

        if not user.check_password(password):
            raise PermissionError("Invalid email or password.")

        if user.is_active == 0:
            raise PermissionError(
                "Account is deactivated. Please contact your company manager."
            )

        if (
            not user.company_id
            and user.role != UserRole.SYSTEM_ADMIN
            and user.role != UserRole.UNASSIGNED_USER
        ):
            raise PermissionError("Account is pending company assignment.")

        company = None
        if user.company_id and user.role != UserRole.SYSTEM_ADMIN:
            company = Company.objects.filter(pk=user.company_id).first()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["name"] = user.name
        refresh["role"] = UserRole(user.role).label
        refresh["shop_name"] = user.shop_name
        refresh["is_active"] = str(user.is_active)
        if company:
            refresh["company_id"] = str(company.id)
        elif user.company_id:
            refresh["company_id"] = str(user.company_id)

        token = str(refresh.access_token)
        refresh_token_str = str(refresh)

        # Save refresh token
        user.refresh_token = refresh_token_str
        user.refresh_token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        user.last_login_at = datetime.now(timezone.utc)
        user.save(update_fields=["refresh_token", "refresh_token_expiry", "last_login_at"])

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company_id": str(company.id) if company else "",
            "company_name": company.name if company else user.shop_name,
            "role": user.role,
            "phone": user.phone,
            "token": token,
            "refresh_token": refresh_token_str,
            "token_expiry": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    @staticmethod
    def refresh_token(refresh_token_str):
        try:
            user = User.objects.get(refresh_token=refresh_token_str)
        except User.DoesNotExist:
            raise ValueError("Invalid refresh token.")

        if (
            user.refresh_token_expiry is None
            or user.refresh_token_expiry <= datetime.now(timezone.utc)
        ):
            raise ValueError("Invalid refresh token.")

        company = None
        if user.company_id:
            company = Company.objects.filter(pk=user.company_id).first()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["name"] = user.name
        refresh["role"] = UserRole(user.role).label
        refresh["shop_name"] = user.shop_name
        refresh["is_active"] = str(user.is_active)
        if company:
            refresh["company_id"] = str(company.id)
        elif user.company_id:
            refresh["company_id"] = str(user.company_id)

        new_token = str(refresh.access_token)
        new_refresh = str(refresh)

        user.refresh_token = new_refresh
        user.refresh_token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        user.save(update_fields=["refresh_token", "refresh_token_expiry"])

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company_id": str(company.id) if company else "",
            "company_name": company.name if company else user.shop_name,
            "role": user.role,
            "phone": user.phone,
            "token": new_token,
            "refresh_token": new_refresh,
            "token_expiry": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    @staticmethod
    def revoke_token(user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return False

        user.refresh_token = None
        user.refresh_token_expiry = None
        user.save(update_fields=["refresh_token", "refresh_token_expiry"])
        return True

    @staticmethod
    def invite_user(data, company_id):
        email = data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValueError("User with this email already exists.")

        company = Company.objects.filter(pk=company_id).first()
        if not company:
            raise ValueError("Company not found.")

        password = data.get("password") or AuthService._generate_random_password()
        user = User(
            email=email,
            name=data["name"],
            shop_name=company.name,
            phone=data.get("phone"),
            password_hash=bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode(),
            company=company,
            role=int(data["role"]),
            is_active=1,
        )
        user.set_password(password)
        user.save()

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["name"] = user.name
        refresh["role"] = UserRole(user.role).label
        refresh["shop_name"] = user.shop_name
        refresh["is_active"] = str(user.is_active)
        refresh["company_id"] = str(company.id)

        token = str(refresh.access_token)
        refresh_token_str = str(refresh)

        user.refresh_token = refresh_token_str
        user.refresh_token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        user.save(update_fields=["refresh_token", "refresh_token_expiry"])

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "company_id": str(company.id),
            "company_name": company.name,
            "role": user.role,
            "phone": user.phone,
            "token": token,
            "refresh_token": refresh_token_str,
            "token_expiry": datetime.now(timezone.utc) + timedelta(hours=1),
        }

    @staticmethod
    def _generate_random_password(length=12):
        chars = string.ascii_letters + string.digits + "!@#$%"
        return "".join(secrets.choice(chars) for _ in range(length))
