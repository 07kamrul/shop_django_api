from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shop.views import auth_views
from shop.views import company_views
from shop.views import product_views
from shop.views import category_views
from shop.views import customer_views
from shop.views import supplier_views
from shop.views import sale_views
from shop.views import inventory_views
from shop.views import report_views
from shop.views import invitation_views

@api_view(["GET"])
def api_root(request):
    return Response({
        "message": "Shop Management API",
        "endpoints": {
            "auth": "/api/auth/",
            "company": "/api/company",
            "products": "/api/products",
            "categories": "/api/categories",
            "customers": "/api/customers",
            "suppliers": "/api/suppliers",
            "sales": "/api/sales",
            "inventory": "/api/inventory/summary",
            "reports": "/api/reports/",
            "invitations": "/api/invitations",
        }
    })


urlpatterns = [
    path("", api_root),

    # Auth
    path("auth/simple-register", auth_views.simple_register),
    path("auth/login", auth_views.login),
    path("auth/refresh-token", auth_views.refresh_token),
    path("auth/revoke-token", auth_views.revoke_token),

    # Company - CRUD
    path("company", company_views.get_company),
    path("company/update", company_views.update_company),
    # Company - Users
    path("company/users", company_views.get_users),
    path("company/users/search", company_views.search_users),
    path("company/users/invite", company_views.invite_user),
    path("company/users/<str:user_id>/role", company_views.update_user_role),
    path("company/users/<str:user_id>", company_views.remove_user),
    path("company/users/<str:user_id>/activate", company_views.activate_user),
    path("company/users/<str:user_id>/deactivate", company_views.deactivate_user),
    path("company/pending-users", company_views.get_pending_users),
    path("company/users/link", company_views.link_user_to_company),
    # Company - System Admin
    path("company/create", company_views.create_company),
    path("company/<str:company_id>/assign-user", company_views.assign_user_to_company),
    path("company/all", company_views.get_all_companies),

    # Products
    path("products", product_views.get_products),
    path("products/low-stock", product_views.get_low_stock_products),
    path("products/create", product_views.create_product),
    path("products/<str:product_id>", product_views.get_product),
    path("products/<str:product_id>/update", product_views.update_product),
    path("products/<str:product_id>/delete", product_views.delete_product),

    # Categories
    path("categories", category_views.get_categories),
    path("categories/create", category_views.create_category),
    path("categories/<str:category_id>", category_views.get_category),
    path("categories/<str:category_id>/update", category_views.update_category),
    path("categories/<str:category_id>/delete", category_views.delete_category),

    # Customers
    path("customers", customer_views.get_customers),
    path("customers/search", customer_views.search_customers),
    path("customers/top", customer_views.get_top_customers),
    path("customers/create", customer_views.create_customer),
    path("customers/<str:customer_id>", customer_views.get_customer),
    path("customers/<str:customer_id>/update", customer_views.update_customer),
    path("customers/<str:customer_id>/delete", customer_views.delete_customer),

    # Suppliers
    path("suppliers", supplier_views.get_suppliers),
    path("suppliers/search", supplier_views.search_suppliers),
    path("suppliers/top", supplier_views.get_top_suppliers),
    path("suppliers/create", supplier_views.create_supplier),
    path("suppliers/<str:supplier_id>", supplier_views.get_supplier),
    path("suppliers/<str:supplier_id>/update", supplier_views.update_supplier),
    path("suppliers/<str:supplier_id>/delete", supplier_views.delete_supplier),

    # Sales
    path("sales", sale_views.get_sales),
    path("sales/today", sale_views.get_today_sales),
    path("sales/create", sale_views.create_sale),
    path("sales/<str:sale_id>", sale_views.get_sale),
    path("sales/<str:sale_id>/update", sale_views.update_sale),
    path("sales/<str:sale_id>/delete", sale_views.delete_sale),

    # Inventory
    path("inventory/summary", inventory_views.get_inventory_summary),
    path("inventory/alerts", inventory_views.get_stock_alerts),
    path("inventory/by-category", inventory_views.get_category_inventory),
    path("inventory/restock-needed", inventory_views.get_products_needing_restock),
    path("inventory/turnover", inventory_views.get_inventory_turnover),

    # Reports
    path("reports/profit-loss", report_views.get_profit_loss_report),
    path("reports/daily-sales", report_views.get_daily_sales_report),
    path("reports/top-products", report_views.get_top_products),

    # Invitations
    path("invitations/test", invitation_views.invitation_test),
    path("invitations", invitation_views.create_invitation),
    path("invitations/accept", invitation_views.accept_invitation),
    path("invitations/claim", invitation_views.claim_invitation),
    path("invitations/my", invitation_views.get_my_invitations),
    path("invitations/<str:invitation_id>/accept", invitation_views.accept_invitation_by_id),
    path("invitations/<str:invitation_id>/reject", invitation_views.reject_invitation),
]
