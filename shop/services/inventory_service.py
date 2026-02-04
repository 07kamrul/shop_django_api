from collections import defaultdict
from decimal import Decimal

from django.db.models import F

from shop.models import Product, Sale, SaleItem


class InventoryService:

    @staticmethod
    def get_inventory_summary(company_id):
        products = Product.objects.filter(company_id=company_id, is_active=True)

        if not products.exists():
            return {
                "total_products": 0,
                "low_stock_items": 0,
                "out_of_stock_items": 0,
                "total_stock_value": Decimal("0"),
                "total_investment": Decimal("0"),
            }

        low_stock = 0
        out_of_stock = 0
        stock_value = Decimal("0")
        investment = Decimal("0")

        for p in products:
            if p.current_stock == 0:
                out_of_stock += 1
            elif p.current_stock <= p.min_stock_level:
                low_stock += 1
            stock_value += p.current_stock * p.selling_price
            investment += p.current_stock * p.buying_price

        return {
            "total_products": products.count(),
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock,
            "total_stock_value": stock_value,
            "total_investment": investment,
        }

    @staticmethod
    def get_stock_alerts(company_id):
        products = (
            Product.objects.filter(
                company_id=company_id,
                is_active=True,
                current_stock__lte=F("min_stock_level"),
            )
            .select_related("category")
            .order_by("current_stock")
        )

        alerts = []
        for p in products:
            alerts.append({
                "product_id": str(p.id),
                "product_name": p.name,
                "category_name": p.category.name if p.category else "Unknown",
                "current_stock": p.current_stock,
                "min_stock_level": p.min_stock_level,
                "alert_type": "out_of_stock" if p.current_stock == 0 else "low_stock",
            })

        alerts.sort(key=lambda a: (0 if a["alert_type"] == "out_of_stock" else 1, a["current_stock"]))
        return alerts

    @staticmethod
    def get_category_inventory(company_id):
        products = (
            Product.objects.filter(company_id=company_id, is_active=True)
            .select_related("category")
        )

        groups = defaultdict(lambda: {
            "category_id": "",
            "category_name": "Uncategorized",
            "product_count": 0,
            "stock_value": Decimal("0"),
            "low_stock_count": 0,
        })

        for p in products:
            key = p.category_id
            groups[key]["category_id"] = str(p.category_id)
            groups[key]["category_name"] = p.category.name if p.category else "Uncategorized"
            groups[key]["product_count"] += 1
            groups[key]["stock_value"] += p.current_stock * p.selling_price
            if p.current_stock <= p.min_stock_level:
                groups[key]["low_stock_count"] += 1

        result = sorted(groups.values(), key=lambda x: x["stock_value"], reverse=True)
        return result

    @staticmethod
    def get_products_needing_restock(company_id):
        return list(
            Product.objects.filter(
                company_id=company_id,
                is_active=True,
                current_stock__lte=F("min_stock_level"),
            ).order_by("current_stock", "name")
        )

    @staticmethod
    def calculate_inventory_turnover(company_id, start_date, end_date):
        sales = Sale.objects.filter(
            company_id=company_id,
            sale_date__gte=start_date,
            sale_date__lte=end_date,
        ).prefetch_related("items")

        cogs = Decimal("0")
        for sale in sales:
            for item in sale.items.all():
                cogs += item.quantity * item.buying_price_at_sale

        if cogs <= 0:
            return Decimal("0")

        products = Product.objects.filter(company_id=company_id, is_active=True)
        current_inv = sum(p.current_stock * p.buying_price for p in products)

        if current_inv <= 0:
            return Decimal("0")

        return round(cogs / current_inv, 2)
