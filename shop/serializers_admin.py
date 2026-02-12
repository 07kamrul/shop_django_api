from rest_framework import serializers
from .models import Company, CompanyStatus, User, UserRole


class PendingCompanySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    business_type = serializers.CharField(allow_null=True)
    description = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.CharField()
    address = serializers.CharField()
    currency = serializers.CharField()
    country = serializers.CharField(allow_null=True)
    status = serializers.IntegerField()
    status_display = serializers.SerializerMethodField()
    owner_id = serializers.CharField()
    owner_name = serializers.CharField()
    owner_email = serializers.CharField()
    owner_phone = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    approved_by_id = serializers.CharField(allow_null=True)
    approved_by_name = serializers.CharField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)

    def get_status_display(self, obj):
        return CompanyStatus(obj["status"]).label


class ApproveCompanySerializer(serializers.Serializer):
    company_id = serializers.CharField()


class RejectCompanySerializer(serializers.Serializer):
    company_id = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)
