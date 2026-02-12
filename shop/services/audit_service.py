import json
from shop.models import AuditLog


class AuditService:
    @staticmethod
    def log(user, action, company=None, entity_type=None, entity_id=None, old_value=None, new_value=None, request=None):
        """Create audit log entry"""
        ip_address = None
        user_agent = None

        if request:
            ip_address = AuditService.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        # Convert dicts to JSON strings
        old_val = json.dumps(old_value) if isinstance(old_value, dict) else old_value
        new_val = json.dumps(new_value) if isinstance(new_value, dict) else new_value

        audit_log = AuditLog.objects.create(
            user=user,
            company=company,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_value=old_val,
            new_value=new_val,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return audit_log

    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def log_company_approval(company, approved_by_user, request=None):
        """Log company approval action"""
        return AuditService.log(
            user=approved_by_user,
            action="COMPANY_APPROVED",
            company=company,
            entity_type="Company",
            entity_id=str(company.id),
            new_value={"company_name": company.name, "owner_email": company.owner.email if company.owner else None},
            request=request
        )

    @staticmethod
    def log_company_rejection(company, rejected_by_user, reason=None, request=None):
        """Log company rejection action"""
        return AuditService.log(
            user=rejected_by_user,
            action="COMPANY_REJECTED",
            company=company,
            entity_type="Company",
            entity_id=str(company.id),
            new_value={"company_name": company.name, "reason": reason},
            request=request
        )

    @staticmethod
    def log_company_suspension(company, suspended_by_user, request=None):
        """Log company suspension action"""
        return AuditService.log(
            user=suspended_by_user,
            action="COMPANY_SUSPENDED",
            company=company,
            entity_type="Company",
            entity_id=str(company.id),
            new_value={"company_name": company.name},
            request=request
        )

    @staticmethod
    def log_user_login(user, request=None):
        """Log user login action"""
        return AuditService.log(
            user=user,
            action="USER_LOGIN",
            company=user.company,
            entity_type="User",
            entity_id=str(user.id),
            request=request
        )

    @staticmethod
    def log_user_registration(user, request=None):
        """Log user registration action"""
        return AuditService.log(
            user=user,
            action="USER_REGISTERED",
            company=user.company,
            entity_type="User",
            entity_id=str(user.id),
            new_value={"email": user.email, "name": user.name},
            request=request
        )

    @staticmethod
    def log_company_creation(company, user, request=None):
        """Log company creation action"""
        return AuditService.log(
            user=user,
            action="COMPANY_CREATED",
            company=company,
            entity_type="Company",
            entity_id=str(company.id),
            new_value={"company_name": company.name},
            request=request
        )
