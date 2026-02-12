from datetime import datetime
from shop.models import Company, CompanyStatus, User, UserRole
from shop.services.audit_service import AuditService


class CompanyService:
    @staticmethod
    def get_pending_companies():
        """Get all pending companies with owner details"""
        companies = Company.objects.filter(status=CompanyStatus.PENDING).select_related("owner", "approved_by")
        result = []
        for company in companies:
            result.append({
                "id": str(company.id),
                "name": company.name,
                "business_type": company.business_type,
                "description": company.description,
                "phone": company.phone,
                "email": company.email,
                "address": company.address,
                "currency": company.currency,
                "country": company.country,
                "status": company.status,
                "owner_id": str(company.owner.id) if company.owner else "",
                "owner_name": company.owner.name if company.owner else "",
                "owner_email": company.owner.email if company.owner else "",
                "owner_phone": company.owner.phone if company.owner else "",
                "created_at": company.created_at,
                "approved_by_id": str(company.approved_by.id) if company.approved_by else None,
                "approved_by_name": company.approved_by.name if company.approved_by else None,
                "approved_at": company.approved_at,
            })
        return result

    @staticmethod
    def approve_company(company_id, approved_by_user, request=None):
        """Approve a company and activate owner"""
        try:
            company = Company.objects.get(pk=company_id)
            company.status = CompanyStatus.APPROVED
            company.approved_by = approved_by_user
            company.approved_at = datetime.now()
            company.save(update_fields=["status", "approved_by", "approved_at"])

            if company.owner:
                company.owner.is_active = 1
                company.owner.save(update_fields=["is_active"])

            # Log approval
            AuditService.log_company_approval(company, approved_by_user, request)

            return True
        except Company.DoesNotExist:
            return False

    @staticmethod
    def reject_company(company_id, rejected_by_user, reason=None, request=None):
        """Reject a company"""
        try:
            company = Company.objects.get(pk=company_id)
            company.status = CompanyStatus.REJECTED
            company.save(update_fields=["status"])

            # Log rejection
            AuditService.log_company_rejection(company, rejected_by_user, reason, request)

            return True
        except Company.DoesNotExist:
            return False

    @staticmethod
    def suspend_company(company_id, suspended_by_user, request=None):
        """Suspend a company and deactivate all users"""
        try:
            company = Company.objects.get(pk=company_id)
            company.status = CompanyStatus.SUSPENDED
            company.save(update_fields=["status"])

            # Deactivate all company users
            User.objects.filter(company=company).update(is_active=0)

            # Log suspension
            AuditService.log_company_suspension(company, suspended_by_user, request)

            return True
        except Company.DoesNotExist:
            return False
