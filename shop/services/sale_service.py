from datetime import datetime, timezone
from decimal import Decimal

from django.db import transaction

from shop.models import (
    Customer,
    Product,
    ProductHistory,
    Sale,
    SaleItem,
)


class SaleService:

    @staticmethod
    def create_sale(data, user):
        company_id = user.company_id
        if not company_id:
            raise PermissionError("User not associated with a company")

        with transaction.atomic():
            total_amount = Decimal("0")
            total_cost = Decimal("0")
            sale_items_data = []
            product_updates = []

            for item_req in data["items"]:
                product = Product.objects.select_for_update().filter(
                    pk=item_req["product_id"], company_id=company_id
                ).first()
                if not product:
                    raise ValueError(f"Product not found: {item_req['product_id']}")

                if product.current_stock < item_req["quantity"]:
                    raise ValueError(f"Insufficient stock for product: {product.name}")

                unit_buying = product.buying_price
                unit_selling = Decimal(str(item_req["unit_selling_price"]))
                qty = item_req["quantity"]
                item_total = qty * unit_selling
                item_cost = qty * unit_buying
                item_profit = item_total - item_cost

                total_amount += item_total
                total_cost += item_cost

                sale_items_data.append({
                    "product": product,
                    "product_name": product.name,
                    "quantity": qty,
                    "unit_buying_price": unit_buying,
                    "unit_selling_price": unit_selling,
                    "total_amount": item_total,
                    "total_cost": item_cost,
                    "total_profit": item_profit,
                })

                stock_before = product.current_stock
                product.current_stock -= qty
                product_updates.append(product)

                ProductHistory.objects.create(
                    product=product,
                    transaction_type="Sale",
                    quantity_changed=-qty,
                    stock_before=stock_before,
                    stock_after=product.current_stock,
                    unit_price=unit_selling,
                    total_value=item_total,
                    notes=f"Sale of {qty} units",
                    created_by=user,
                    company_id=company_id,
                )

            # Update customer stats
            customer = None
            customer_id = data.get("customer_id")
            if customer_id:
                customer = Customer.objects.filter(
                    pk=customer_id, company_id=company_id
                ).first()
                if customer:
                    customer.total_purchases += total_amount
                    customer.total_transactions += 1
                    customer.last_purchase_date = datetime.now(timezone.utc)
                    customer.save(update_fields=[
                        "total_purchases", "total_transactions", "last_purchase_date",
                    ])

            sale = Sale.objects.create(
                customer_id=customer_id if customer_id else None,
                customer_name=data.get("customer_name") or (customer.name if customer else None),
                customer_phone=data.get("customer_phone") or (customer.phone if customer else None),
                payment_method=data.get("payment_method", "cash"),
                total_amount=total_amount,
                total_cost=total_cost,
                total_profit=total_amount - total_cost,
                created_by=user,
                company_id=company_id,
            )

            for item_data in sale_items_data:
                SaleItem.objects.create(
                    sale=sale,
                    product=item_data["product"],
                    product_name=item_data["product_name"],
                    quantity=item_data["quantity"],
                    unit_buying_price=item_data["unit_buying_price"],
                    unit_selling_price=item_data["unit_selling_price"],
                    total_amount=item_data["total_amount"],
                    total_cost=item_data["total_cost"],
                    total_profit=item_data["total_profit"],
                )

            for p in product_updates:
                p.save(update_fields=["current_stock"])

            return sale

    @staticmethod
    def update_sale(sale_id, data, user):
        company_id = user.company_id
        if not company_id:
            raise PermissionError("User not associated with a company")

        with transaction.atomic():
            sale = Sale.objects.filter(pk=sale_id, company_id=company_id).first()
            if not sale:
                return None

            existing_items = list(SaleItem.objects.filter(sale=sale))
            previous_total = sale.total_amount or Decimal("0")

            # Restore stock for existing items
            for item in existing_items:
                product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                if product:
                    stock_before = product.current_stock
                    product.current_stock += item.quantity
                    product.save(update_fields=["current_stock"])

                    ProductHistory.objects.create(
                        product=product,
                        transaction_type="Sale Update (Reversal)",
                        quantity_changed=item.quantity,
                        stock_before=stock_before,
                        stock_after=product.current_stock,
                        unit_price=item.unit_selling_price,
                        total_value=item.total_amount,
                        notes=f"Reversal before sale update - restored {item.quantity} units",
                        created_by=user,
                        company_id=company_id,
                    )

            SaleItem.objects.filter(sale=sale).delete()

            new_total = Decimal("0")
            new_cost = Decimal("0")

            for item_req in data["items"]:
                product = Product.objects.select_for_update().filter(
                    pk=item_req["product_id"], company_id=company_id
                ).first()
                if not product:
                    raise ValueError(f"Product not found: {item_req['product_id']}")

                qty = item_req["quantity"]
                if product.current_stock < qty:
                    raise ValueError(f"Insufficient stock for product: {product.name}")

                unit_buying = product.buying_price
                unit_selling = Decimal(str(item_req["unit_selling_price"]))
                item_total = qty * unit_selling
                item_cost = qty * unit_buying
                item_profit = item_total - item_cost

                new_total += item_total
                new_cost += item_cost

                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    product_name=product.name,
                    quantity=qty,
                    unit_buying_price=unit_buying,
                    unit_selling_price=unit_selling,
                    total_amount=item_total,
                    total_cost=item_cost,
                    total_profit=item_profit,
                )

                stock_before = product.current_stock
                product.current_stock -= qty
                product.save(update_fields=["current_stock"])

                ProductHistory.objects.create(
                    product=product,
                    transaction_type="Sale Update",
                    quantity_changed=-qty,
                    stock_before=stock_before,
                    stock_after=product.current_stock,
                    unit_price=unit_selling,
                    total_value=item_total,
                    notes=f"Sale update - sold {qty} units",
                    created_by=user,
                    company_id=company_id,
                )

            # Update customer statistics
            if sale.customer_id:
                old_customer = Customer.objects.filter(
                    pk=sale.customer_id, company_id=company_id
                ).first()
                if old_customer:
                    old_customer.total_purchases -= previous_total
                    old_customer.total_purchases += new_total
                    old_customer.last_purchase_date = datetime.now(timezone.utc)
                    old_customer.save(update_fields=["total_purchases", "last_purchase_date"])

            new_customer_id = data.get("customer_id")
            if new_customer_id and new_customer_id != sale.customer_id:
                if sale.customer_id:
                    old_cust = Customer.objects.filter(
                        pk=sale.customer_id, company_id=company_id
                    ).first()
                    if old_cust:
                        old_cust.total_purchases -= new_total
                        old_cust.total_transactions -= 1
                        old_cust.save(update_fields=["total_purchases", "total_transactions"])

                new_cust = Customer.objects.filter(
                    pk=new_customer_id, company_id=company_id
                ).first()
                if new_cust:
                    new_cust.total_purchases += new_total
                    new_cust.total_transactions += 1
                    new_cust.last_purchase_date = datetime.now(timezone.utc)
                    new_cust.save(update_fields=[
                        "total_purchases", "total_transactions", "last_purchase_date",
                    ])

            sale.customer_id = data.get("customer_id") or sale.customer_id
            sale.customer_name = data.get("customer_name") or sale.customer_name
            sale.customer_phone = data.get("customer_phone") or sale.customer_phone
            sale.payment_method = data.get("payment_method") or sale.payment_method
            sale.total_amount = new_total
            sale.total_cost = new_cost
            sale.total_profit = new_total - new_cost
            sale.save()

            return sale

    @staticmethod
    def get_sale_by_id(sale_id, company_id):
        return Sale.objects.prefetch_related("items").filter(
            pk=sale_id, company_id=company_id
        ).first()

    @staticmethod
    def get_sales(company_id, start_date=None, end_date=None):
        qs = Sale.objects.prefetch_related("items").filter(
            company_id=company_id
        )
        if start_date:
            qs = qs.filter(sale_date__gte=start_date)
        if end_date:
            qs = qs.filter(sale_date__lte=end_date)
        return qs.order_by("-sale_date")

    @staticmethod
    def delete_sale(sale_id, user):
        company_id = user.company_id
        if not company_id:
            raise PermissionError("User not associated with a company")

        with transaction.atomic():
            sale = Sale.objects.filter(pk=sale_id, company_id=company_id).first()
            if not sale:
                return False

            items = SaleItem.objects.filter(sale=sale)
            for item in items:
                product = Product.objects.select_for_update().filter(pk=item.product_id).first()
                if product:
                    stock_before = product.current_stock
                    product.current_stock += item.quantity
                    product.save(update_fields=["current_stock"])

                    ProductHistory.objects.create(
                        product=product,
                        transaction_type="Sale Cancellation",
                        quantity_changed=item.quantity,
                        stock_before=stock_before,
                        stock_after=product.current_stock,
                        unit_price=item.unit_selling_price,
                        total_value=item.total_amount,
                        notes=f"Sale cancellation - restored {item.quantity} units",
                        created_by=user,
                        company_id=company_id,
                    )

            if sale.customer_id:
                customer = Customer.objects.filter(
                    pk=sale.customer_id, company_id=company_id
                ).first()
                if customer:
                    customer.total_purchases -= sale.total_amount or Decimal("0")
                    customer.total_transactions -= 1
                    customer.save(update_fields=["total_purchases", "total_transactions"])

            items.delete()
            sale.delete()
            return True

    @staticmethod
    def get_today_sales(company_id):
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + __import__("datetime").timedelta(days=1)
        return SaleService.get_sales(company_id, start_date=today, end_date=tomorrow)
