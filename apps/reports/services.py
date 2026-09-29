"""
MERRIGE ERP - Тайлангийн Service Layer
Борлуулалт, Ашиг, Шимтгэл, Агуулах, Борлуулагчийн тайлан, Топ бараа, Топ
борлуулагчийн тооцооллыг эндээс гүйцэтгэнэ. Views нимгэн хэвээр байлгаж,
өгөгдөл нэгтгэх бүх логикийг Service Layer-т төвлөрүүлнэ.

RBAC: Order/Commission-той ижил гурван шатлал (Админ бүгд, Үндсэн
Борлуулагч өөрийн + Гэрээт Борлуулагчдаа, Гэрээт Борлуулагч зөвхөн өөрийн).
Ашгийн тайлан (Анхны үнэ, Нийт зардал зэрэг нууц мэдээлэл) зөвхөн Админ-д
зориулагдсан тул RBAC шүүлтгүй, шууд Админ endpoint-оор хамгаалагдана.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone

from apps.commissions.repositories import CommissionRepository
from apps.inventory.repositories import InventoryRepository
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.orders.repositories import OrderRepository
from apps.profits.services import ProfitService
from apps.shared.exceptions import БизнесАлдаа

MONEY_FIELD = DecimalField(max_digits=16, decimal_places=2)
LOW_STOCK_THRESHOLD = 5


def _line_total_expression():
    return ExpressionWrapper(F("unit_price") * F("quantity"), output_field=MONEY_FIELD)


def resolve_date_range(start_date, end_date):
    if end_date is None:
        end_date = timezone.localdate()
    if start_date is None:
        start_date = end_date - timedelta(days=30)
    if start_date > end_date:
        raise БизнесАлдаа("Эхлэх огноо дуусах огнооноос хойш байж болохгүй.")
    return start_date, end_date


class ReportService:
    # ------------------------------------------------------------------
    # Борлуулалтын тайлан
    # ------------------------------------------------------------------
    @staticmethod
    def sales_report(user, start_date=None, end_date=None):
        start_date, end_date = resolve_date_range(start_date, end_date)
        orders = OrderRepository.list_visible_to(user).filter(
            status=OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        total_orders = orders.count()
        total_sales = OrderItem.objects.filter(order__in=orders).aggregate(
            total=Sum(_line_total_expression())
        )["total"] or Decimal("0")

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_orders": total_orders,
            "total_sales": total_sales,
        }

    # ------------------------------------------------------------------
    # Ашгийн тайлан (зөвхөн Админ - НУУЦ МЭДЭЭЛЭЛ)
    # ------------------------------------------------------------------
    @staticmethod
    def profit_report(start_date=None, end_date=None):
        start_date, end_date = resolve_date_range(start_date, end_date)
        orders = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        ).prefetch_related("items__variant__product")

        total_revenue = Decimal("0")
        total_cost = Decimal("0")
        total_net_profit = Decimal("0")
        total_owner_profit = Decimal("0")

        for order in orders:
            for item in order.items.all():
                product = item.variant.product
                try:
                    breakdown = ProfitService.calculate_breakdown(product)
                except БизнесАлдаа:
                    continue  # Өртгийн мэдээлэлгүй бараа тооцооноос гадуур
                total_revenue += item.unit_price * item.quantity
                total_cost += breakdown["total_cost"] * item.quantity
                total_net_profit += breakdown["net_profit"] * item.quantity
                total_owner_profit += breakdown["owner_profit"] * item.quantity

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_net_profit": total_net_profit,
            "total_owner_profit": total_owner_profit,
        }

    # ------------------------------------------------------------------
    # Шимтгэлийн тайлан
    # ------------------------------------------------------------------
    @staticmethod
    def commission_report(user, start_date=None, end_date=None):
        start_date, end_date = resolve_date_range(start_date, end_date)
        commissions = CommissionRepository.list_visible_to(user).filter(
            created_at__date__gte=start_date, created_at__date__lte=end_date
        )
        total_amount = commissions.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        by_seller = list(
            commissions.values("seller__id", "seller__first_name", "seller__last_name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_amount": total_amount,
            "by_seller": by_seller,
        }

    # ------------------------------------------------------------------
    # Агуулахын тайлан (Үлдэгдлийн дүн RRP-ээр, нууц өртгөөр биш)
    # ------------------------------------------------------------------
    @staticmethod
    def inventory_report():
        stocks = InventoryRepository.list_stock()
        total_quantity = 0
        total_retail_value = Decimal("0")
        low_stock_count = 0

        for stock in stocks:
            total_quantity += stock.quantity
            total_retail_value += stock.quantity * stock.variant.product.price
            if stock.quantity <= LOW_STOCK_THRESHOLD:
                low_stock_count += 1

        return {
            "total_variants": stocks.count(),
            "total_quantity": total_quantity,
            "total_retail_value": total_retail_value,
            "low_stock_count": low_stock_count,
        }

    # ------------------------------------------------------------------
    # Борлуулагчийн тайлан / Топ борлуулагч
    # ------------------------------------------------------------------
    @staticmethod
    def seller_report(user, start_date=None, end_date=None):
        start_date, end_date = resolve_date_range(start_date, end_date)
        orders = (
            OrderRepository.list_visible_to(user)
            .filter(
                status=OrderStatus.COMPLETED,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .select_related("seller")
            .prefetch_related("items")
        )

        sellers = {}
        for order in orders:
            seller = order.seller
            entry = sellers.setdefault(
                seller.id,
                {
                    "seller_name": seller.get_full_name(),
                    "order_count": 0,
                    "total_sales": Decimal("0"),
                },
            )
            entry["order_count"] += 1
            for item in order.items.all():
                entry["total_sales"] += item.unit_price * item.quantity

        return sorted(sellers.values(), key=lambda row: row["total_sales"], reverse=True)

    @staticmethod
    def top_sellers(user, start_date=None, end_date=None, limit=10):
        return ReportService.seller_report(user, start_date, end_date)[:limit]

    # ------------------------------------------------------------------
    # Топ бараа
    # ------------------------------------------------------------------
    @staticmethod
    def top_products(user, start_date=None, end_date=None, limit=10):
        start_date, end_date = resolve_date_range(start_date, end_date)
        orders = OrderRepository.list_visible_to(user).filter(
            status=OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
        )
        items = OrderItem.objects.filter(order__in=orders).select_related(
            "variant__product"
        )

        products = {}
        for item in items:
            product = item.variant.product
            entry = products.setdefault(
                product.id,
                {
                    "product_code": product.code,
                    "product_name": product.name,
                    "quantity_sold": 0,
                    "revenue": Decimal("0"),
                },
            )
            entry["quantity_sold"] += item.quantity
            entry["revenue"] += item.unit_price * item.quantity

        ranked = sorted(products.values(), key=lambda row: row["quantity_sold"], reverse=True)
        return ranked[:limit]
