from rest_framework.permissions import BasePermission

from shop.models import UserRole


class IsActiveUser(BasePermission):
    """Equivalent to ActiveUserOnly policy."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_active != 1:
            return False
        # Must have company OR be SystemAdmin
        if user.company_id or user.role == UserRole.SYSTEM_ADMIN:
            return True
        return False


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.OWNER
        )


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.SYSTEM_ADMIN
        )


class IsManagerOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (UserRole.OWNER, UserRole.MANAGER)


class IsStaffOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (
            UserRole.SYSTEM_ADMIN,
            UserRole.OWNER,
            UserRole.MANAGER,
            UserRole.STAFF,
        )


class IsOwnerOrSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (UserRole.OWNER, UserRole.SYSTEM_ADMIN)


class HasCompany(BasePermission):
    """Check if user has a company assigned."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.company_id is not None
