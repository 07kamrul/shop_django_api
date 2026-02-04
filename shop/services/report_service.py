from collections import defaultdict
from decimal import Decimal
from itertools import groupby

from shop.models import Category, Product, Sale, SaleItem


class ReportService:

    @staticmethod
    def get_profit_loss_report(company_id, start_date, end_date):
        sales = Sale.objects.filter(
            company_id=company_id,
            sale_date__gte=start_date,
            sale_date__lte=end_date,
        )

        total_revenue = sum(s.total_amount or Decimal("0") for s in sales)
        total_cost = sum(s.total_cost or Decimal("0") for s in sales)
        gross_profit = total_revenue - total_cost
        margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")

        categories = Category.objects.filter(company_id=company_id)
        breakdown = []

        for cat in categories:
            product_ids = list(
                Product.objects.filter(category=cat, company_id=company_id)
                .values_list("id", flat=True)
            )
            if not product_ids:
                continue

            cat_items = SaleItem.objects.filter(
                product_id__in=product_ids,
                sale__sale_date__gte=start_date,
                sale__sale_date__lte=end_date,
                sale__company_id=company_id,
            )

            cat_sales = sum(si.total_amount or Decimal("0") for si in cat_items)
            cat_profit = sum(si.total_profit or Decimal("0") for si in cat_items)
            cat_margin = (cat_profit / cat_sales * 100) if cat_sales > 0 else Decimal("0")

            breakdown.append({
                "category_id": str(cat.id),
                "category_name": cat.name,
                "total_sales": cat_sales,
                "total_profit": cat_profit,
                "profit_margin": cat_margin,
            })

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
            "gross_profit_margin": margin,
            "category_breakdown": breakdown,
        }

    @staticmethod
    def get_daily_sales_report(company_id, start_date, end_date):
        sales = list(
            Sale.objects.filter(
                company_id=company_id,
                sale_date__gte=start_date,
                sale_date__lte=end_date,
            ).order_by("-sale_date")
        )

        daily_groups = defaultdict(list)
        for s in sales:
            daily_groups[s.sale_date.date()].append(s)

        reports = []
        for date_key in sorted(daily_groups.keys(), reverse=True):
            day_sales = daily_groups[date_key]
            total_sales = sum(s.total_amount or Decimal("0") for s in day_sales)
            total_profit = sum(s.total_profit or Decimal("0") for s in day_sales)

            sale_ids = [s.id for s in day_sales]
            items = SaleItem.objects.filter(sale_id__in=sale_ids)

            product_agg = defaultdict(lambda: {
                "product_id": "",
                "product_name": "",
                "quantity_sold": 0,
                "total_sales": Decimal("0"),
                "total_profit": Decimal("0"),
            })
            for si in items:
                key = si.product_id
                product_agg[key]["product_id"] = str(si.product_id)
                product_agg[key]["product_name"] = si.product_name
                product_agg[key]["quantity_sold"] += si.quantity
                product_agg[key]["total_sales"] += si.total_amount or Decimal("0")
                product_agg[key]["total_profit"] += si.total_profit or Decimal("0")

            top_products = sorted(
                product_agg.values(), key=lambda x: x["total_sales"], reverse=True
            )[:5]

            reports.append({
                "date": date_key,
                "total_sales": total_sales,
                "total_profit": total_profit,
                "total_transactions": len(day_sales),
                "top_products": top_products,
            })

        return reports

    @staticmethod
    def get_top_selling_products(company_id, start_date, end_date, limit=10):
        sales = Sale.objects.filter(
            company_id=company_id,
            sale_date__gte=start_date,
            sale_date__lte=end_date,
        )
        sale_ids = list(sales.values_list("id", flat=True))
        items = SaleItem.objects.filter(sale_id__in=sale_ids)

        product_agg = defaultdict(lambda: {
            "product_id": "",
            "product_name": "",
            "quantity_sold": 0,
            "total_sales": Decimal("0"),
            "total_profit": Decimal("0"),
        })
        for si in items:
            key = si.product_id
            product_agg[key]["product_id"] = str(si.product_id)
            product_agg[key]["product_name"] = si.product_name
            product_agg[key]["quantity_sold"] += si.quantity
            product_agg[key]["total_sales"] += si.total_amount or Decimal("0")
            product_agg[key]["total_profit"] += si.total_profit or Decimal("0")

        top = sorted(product_agg.values(), key=lambda x: x["total_sales"], reverse=True)[:limit]
        return top
