from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    Branch,
    Category,
    Company,
    Customer,
    Invitation,
    Product,
    ProductHistory,
    Sale,
    SaleItem,
    Supplier,
    User,
    UserRole,
)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class SimpleRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6)
    name = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class AuthResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    company_id = serializers.CharField(allow_blank=True, allow_null=True)
    company_name = serializers.CharField(allow_blank=True, allow_null=True)
    branch_id = serializers.CharField(allow_blank=True, allow_null=True)
    branch_name = serializers.CharField(allow_blank=True, allow_null=True)
    role = serializers.SerializerMethodField()
    phone = serializers.CharField(allow_null=True)
    token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_expiry = serializers.DateTimeField()
    has_company = serializers.BooleanField()
    has_branch = serializers.BooleanField()

    def get_role(self, obj):
        return UserRole(obj["role"]).label


class PendingUserResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    message = serializers.CharField()


class InviteUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.STAFF)
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["name"] = user.name
        token["role"] = UserRole(user.role).label
        token["shop_name"] = user.shop_name
        token["is_active"] = str(user.is_active)
        if user.company_id:
            token["company_id"] = str(user.company_id)
        return token


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------
class CompanyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id", "name", "description", "phone", "email", "address",
            "logo_url", "currency", "timezone", "is_active",
            "created_at", "updated_at",
        ]


class CompanyUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    logo_url = serializers.CharField(max_length=255, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=50, required=False)
    timezone = serializers.CharField(max_length=50, required=False)


class CompanyUserResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    role = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()
    shop_name = serializers.CharField(allow_null=True)
    last_login_at = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField()

    def get_role(self, obj):
        role_val = obj["role"] if isinstance(obj, dict) else obj.role
        return UserRole(role_val).label


class UpdateUserRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=UserRole.choices)


class LinkUserToCompanySerializer(serializers.Serializer):
    user_id = serializers.CharField()
    role = serializers.ChoiceField(choices=UserRole.choices, default=UserRole.STAFF)


class CreateCompanySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    address = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    currency = serializers.CharField(default="BDT")
    timezone = serializers.CharField(default="Asia/Dhaka")


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------
class BranchResponseSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Branch
        fields = [
            "id", "name", "company_id", "company_name", "address",
            "phone", "email", "is_active", "is_main", "created_at", "updated_at",
        ]


class BranchCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    address = serializers.CharField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    is_main = serializers.BooleanField(default=False)


class BranchUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    is_main = serializers.BooleanField(required=False)


class SelectBranchSerializer(serializers.Serializer):
    branch_id = serializers.CharField()


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    barcode = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    category_id = serializers.CharField()
    buying_price = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    selling_price = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    current_stock = serializers.IntegerField(min_value=0)
    min_stock_level = serializers.IntegerField(min_value=0, default=10)
    supplier_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ProductResponseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", default="Unknown")
    supplier_name = serializers.SerializerMethodField()
    profit_per_unit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    profit_margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "barcode", "category_id", "category_name",
            "buying_price", "selling_price", "current_stock", "min_stock_level",
            "supplier_id", "supplier_name", "created_at", "is_active",
            "profit_per_unit", "profit_margin", "is_low_stock",
        ]

    def get_supplier_name(self, obj):
        if obj.supplier:
            return obj.supplier.name
        return None


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class CategoryCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    parent_category_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    profit_margin_target = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True,
        min_value=0, max_value=100,
    )


class SubCategoryResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    parent_category_id = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    profit_margin_target = serializers.DecimalField(
        max_digits=5, decimal_places=2, allow_null=True
    )
    created_at = serializers.DateTimeField()
    product_count = serializers.IntegerField()


class CategoryResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    parent_category_id = serializers.CharField(allow_null=True)
    parent_category_name = serializers.CharField(allow_null=True)
    description = serializers.CharField(allow_null=True)
    profit_margin_target = serializers.DecimalField(
        max_digits=5, decimal_places=2, allow_null=True
    )
    created_at = serializers.DateTimeField()
    product_count = serializers.IntegerField()
    sub_categories = SubCategoryResponseSerializer(many=True, required=False)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class CustomerCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class CustomerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id", "name", "phone", "email", "address",
            "total_purchases", "total_transactions",
            "last_purchase_date", "created_at",
        ]


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------
class SupplierCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    contact_person = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class SupplierResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "name", "contact_person", "phone", "email", "address",
            "total_purchases", "total_products",
            "last_purchase_date", "created_at",
        ]


# ---------------------------------------------------------------------------
# Sale
# ---------------------------------------------------------------------------
class SaleItemRequestSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    unit_selling_price = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)


class SaleCreateSerializer(serializers.Serializer):
    customer_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    payment_method = serializers.CharField(default="cash")
    items = SaleItemRequestSerializer(many=True)


class SaleItemResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        fields = [
            "id", "product_id", "product_name", "quantity",
            "unit_buying_price", "unit_selling_price",
            "total_amount", "total_cost", "total_profit",
        ]


class SaleResponseSerializer(serializers.ModelSerializer):
    items = SaleItemResponseSerializer(many=True, read_only=True)

    class Meta:
        model = Sale
        fields = [
            "id", "sale_date", "customer_id", "customer_name", "customer_phone",
            "payment_method", "total_amount", "total_cost", "total_profit",
            "created_at", "items",
        ]


class SaleItemUpdateSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    quantity = serializers.IntegerField(min_value=1)
    unit_selling_price = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)


class SaleUpdateSerializer(serializers.Serializer):
    customer_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    customer_phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    payment_method = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = SaleItemUpdateSerializer(many=True)


# ---------------------------------------------------------------------------
# Inventory DTOs
# ---------------------------------------------------------------------------
class InventorySummarySerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    low_stock_items = serializers.IntegerField()
    out_of_stock_items = serializers.IntegerField()
    total_stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_investment = serializers.DecimalField(max_digits=15, decimal_places=2)


class StockAlertSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    category_name = serializers.CharField()
    current_stock = serializers.IntegerField()
    min_stock_level = serializers.IntegerField()
    alert_type = serializers.CharField()


class CategoryInventorySerializer(serializers.Serializer):
    category_id = serializers.CharField()
    category_name = serializers.CharField()
    product_count = serializers.IntegerField()
    stock_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    low_stock_count = serializers.IntegerField()


# ---------------------------------------------------------------------------
# Report DTOs
# ---------------------------------------------------------------------------
class ProductSalesSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    quantity_sold = serializers.IntegerField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)


class DailySalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_transactions = serializers.IntegerField()
    top_products = ProductSalesSerializer(many=True)


class CategoryReportSerializer(serializers.Serializer):
    category_id = serializers.CharField()
    category_name = serializers.CharField()
    total_sales = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    profit_margin = serializers.DecimalField(max_digits=10, decimal_places=2)


class ProfitLossReportSerializer(serializers.Serializer):
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
    gross_profit = serializers.DecimalField(max_digits=15, decimal_places=2)
    gross_profit_margin = serializers.DecimalField(max_digits=10, decimal_places=2)
    category_breakdown = CategoryReportSerializer(many=True)


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------
class CreateInvitationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserRole.choices)
    company_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class AcceptInvitationSerializer(serializers.Serializer):
    token = serializers.CharField()
    name = serializers.CharField()
    password = serializers.CharField()
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class InvitationResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField()
    token = serializers.CharField()
    role = serializers.SerializerMethodField()
    company_id = serializers.CharField(allow_null=True)
    expires_at = serializers.DateTimeField()

    def get_role(self, obj):
        role_val = obj["role"] if isinstance(obj, dict) else obj.role
        return UserRole(role_val).label
