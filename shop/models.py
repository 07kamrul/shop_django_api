import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserRole(models.IntegerChoices):
    SYSTEM_ADMIN = 0, "SystemAdmin"
    OWNER = 1, "Owner"
    MANAGER = 2, "Manager"
    STAFF = 3, "Staff"
    UNASSIGNED_USER = 4, "UnAssignedUser"


# ---------------------------------------------------------------------------
# Custom user manager
# ---------------------------------------------------------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.SYSTEM_ADMIN)
        extra_fields.setdefault("is_active", 1)
        extra_fields.setdefault("shop_name", "System")
        extra_fields.setdefault("name", "System Admin")
        return self.create_user(email, password, **extra_fields)


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------
class CompanyStatus(models.IntegerChoices):
    PENDING = 0, "Pending"
    APPROVED = 1, "Approved"
    REJECTED = 2, "Rejected"
    SUSPENDED = 3, "Suspended"


class Company(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False, db_column="Id")
    name = models.CharField(max_length=255, db_column="Name")
    business_type = models.CharField(max_length=50, blank=True, null=True, db_column="BusinessType")
    description = models.CharField(max_length=500, blank=True, default="", db_column="Description")
    phone = models.CharField(max_length=20, blank=True, default="", db_column="Phone")
    email = models.EmailField(max_length=255, blank=True, default="", db_column="Email")
    address = models.TextField(blank=True, default="", db_column="Address")
    logo_url = models.CharField(max_length=255, blank=True, default="", db_column="LogoUrl")
    currency = models.CharField(max_length=50, default="BDT", db_column="Currency")
    country = models.CharField(max_length=100, blank=True, null=True, db_column="Country")
    timezone = models.CharField(max_length=50, default="Asia/Dhaka", db_column="Timezone")
    is_active = models.BooleanField(default=True, db_column="IsActive")
    status = models.IntegerField(choices=CompanyStatus.choices, default=CompanyStatus.PENDING, db_column="Status")
    created_at = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    updated_at = models.DateTimeField(auto_now=True, db_column="UpdatedAt")
    owner = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies",
        db_column="OwnerId"
    )
    approved_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_companies",
        db_column="ApprovedBy"
    )
    approved_at = models.DateTimeField(null=True, blank=True, db_column="ApprovedAt")

    class Meta:
        db_table = "companies"
        indexes = [models.Index(fields=["owner"])]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Branch
# ---------------------------------------------------------------------------
class Branch(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="branches")
    address = models.TextField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_branches",
    )

    class Meta:
        db_table = "branches"
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["company", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"


# ---------------------------------------------------------------------------
# User (custom auth model)
# ---------------------------------------------------------------------------
class User(AbstractBaseUser):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False, db_column="Id")
    email = models.EmailField(max_length=255, unique=True, db_column="Email")
    name = models.CharField(max_length=255, db_column="Name")
    phone = models.CharField(max_length=20, blank=True, null=True, db_column="Phone")
    is_active = models.IntegerField(default=0, db_column="IsActive")
    last_login = models.DateTimeField(blank=True, null=True, db_column="LastLoginAt")
    shop_name = models.CharField(max_length=255, default="", db_column="ShopName")
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        db_column="CompanyId"
    )
    branch = models.ForeignKey(
        "Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        db_column="BranchId",
    )
    role = models.IntegerField(choices=UserRole.choices, default=UserRole.STAFF, db_column="Role")
    password = models.CharField(max_length=255, default="", db_column="PasswordHash")
    created_at = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")
    is_email_verified = models.BooleanField(default=False, db_column="IsEmailVerified")
    refresh_token = models.CharField(max_length=255, blank=True, null=True, db_column="RefreshToken")
    refresh_token_expiry = models.DateTimeField(blank=True, null=True, db_column="RefreshTokenExpiryTime")

    # Required by AbstractBaseUser
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

    @property
    def is_active_bool(self):
        return self.is_active == 1


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------
class EmailVerification(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False, db_column="Id")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_verifications", db_column="UserId")
    email = models.EmailField(max_length=255, db_column="Email")
    otp = models.CharField(max_length=6, db_column="Otp")
    is_verified = models.BooleanField(default=False, db_column="IsVerified")
    expires_at = models.DateTimeField(db_column="ExpiresAt")
    created_at = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = "email_verifications"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["email"]),
        ]


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------
class AuditLog(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False, db_column="Id")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs", db_column="UserId")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs", db_column="CompanyId")
    action = models.CharField(max_length=255, db_column="Action")
    entity_type = models.CharField(max_length=100, null=True, blank=True, db_column="EntityType")
    entity_id = models.CharField(max_length=36, null=True, blank=True, db_column="EntityId")
    old_value = models.TextField(null=True, blank=True, db_column="OldValue")
    new_value = models.TextField(null=True, blank=True, db_column="NewValue")
    ip_address = models.CharField(max_length=45, null=True, blank=True, db_column="IpAddress")
    user_agent = models.CharField(max_length=255, null=True, blank=True, db_column="UserAgent")
    created_at = models.DateTimeField(auto_now_add=True, db_column="CreatedAt")

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["company"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class Category(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    parent_category = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="sub_categories",
    )
    description = models.TextField(blank=True, null=True)
    profit_margin_target = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="categories")

    class Meta:
        db_table = "categories"
        indexes = [models.Index(fields=["company"])]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class Product(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.RESTRICT, related_name="products")
    buying_price = models.DecimalField(max_digits=15, decimal_places=2)
    selling_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_stock = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=10)
    supplier = models.ForeignKey(
        "Supplier",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="products")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="products")

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["company", "is_active"]),
        ]

    def __str__(self):
        return self.name

    @property
    def profit_per_unit(self):
        return self.selling_price - self.buying_price

    @property
    def profit_margin(self):
        if self.selling_price > 0:
            return (self.profit_per_unit / self.selling_price) * 100
        return 0

    @property
    def is_low_stock(self):
        return self.current_stock <= self.min_stock_level


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class Customer(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_purchases = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_transactions = models.IntegerField(default=0)
    last_purchase_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="customers")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="customers")

    class Meta:
        db_table = "customers"
        indexes = [models.Index(fields=["company"])]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Supplier
# ---------------------------------------------------------------------------
class Supplier(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    total_purchases = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_products = models.IntegerField(default=0)
    last_purchase_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="suppliers")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="suppliers")

    class Meta:
        db_table = "suppliers"
        indexes = [models.Index(fields=["company"])]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Sale
# ---------------------------------------------------------------------------
class Sale(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    sale_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="cash")
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sales")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="sales")

    class Meta:
        db_table = "sales"
        indexes = [
            models.Index(fields=["sale_date"]),
            models.Index(fields=["created_by"]),
            models.Index(fields=["company"]),
            models.Index(fields=["company", "sale_date"]),
        ]

    def __str__(self):
        return f"Sale {self.id}"


# ---------------------------------------------------------------------------
# SaleItem
# ---------------------------------------------------------------------------
class SaleItem(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, related_name="sale_items")
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    buying_price_at_sale = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unit_buying_price = models.DecimalField(max_digits=15, decimal_places=2)
    unit_selling_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    class Meta:
        db_table = "sale_items"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"


# ---------------------------------------------------------------------------
# ProductHistory
# ---------------------------------------------------------------------------
class ProductHistory(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="histories")
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=50)
    quantity_changed = models.IntegerField()
    stock_before = models.IntegerField()
    stock_after = models.IntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="product_histories")
    company = models.ForeignKey(Company, on_delete=models.RESTRICT, related_name="product_histories")

    class Meta:
        db_table = "product_histories"
        indexes = [models.Index(fields=["company"])]


# ---------------------------------------------------------------------------
# Invitation
# ---------------------------------------------------------------------------
class Invitation(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField()
    role = models.IntegerField(choices=UserRole.choices)
    company_id = models.CharField(max_length=36, blank=True, null=True)
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    invited_by_user_id = models.CharField(max_length=36, default="")

    class Meta:
        db_table = "invitations"
        indexes = [models.Index(fields=["email"])]

    def __str__(self):
        return f"Invitation for {self.email}"
