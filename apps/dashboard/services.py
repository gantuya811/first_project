"""
MERRIGE ERP - Admin Dashboard Service Layer
Зөвхөн Админ дэлгэцэнд зориулсан KPI, график, "анхаарах" мэдээллийг
apps.reports/apps.inventory/apps.payments/apps.commissions-ийн Service/
Repository давхаргыг ДАХИН АШИГЛАН нэгтгэнэ — тооцооллын логикийг энд
давхардуулахгүй, зөвхөн бүтэц/бүлэглэлт нэмнэ.
"""

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import User
from apps.commissions.models import Commission
from apps.inventory.repositories import InventoryRepository
from apps.orders.models import Order, OrderStatus
from apps.payments.repositories import PaymentRepository
from apps.profits.services import ProfitService
from apps.reports.services import ReportService, resolve_date_range
from apps.shared.exceptions import БизнесАлдаа


class DashboardService:
    @staticmethod
    def kpi_summary(admin_user):
        """Спецификейшнд заасан 10 KPI-г нэг дор буцаана."""
        today = timezone.localdate()
        month_start = today.replace(day=1)

        today_orders_count = Order.objects.filter(created_at__date=today).count()

        today_sales = ReportService.sales_report(admin_user, today, today)
        today_profit = ReportService.profit_report(today, today)

        month_sales = ReportService.sales_report(admin_user, month_start, today)
        month_profit = ReportService.profit_report(month_start, today)

        month_commissions = Commission.objects.filter(
            created_at__date__gte=month_start, created_at__date__lte=today
        )
        main_seller_commission = month_commissions.filter(
            seller__role=User.Role.MAIN_SELLER
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        contract_seller_commission = month_commissions.filter(
            seller__role=User.Role.CONTRACT_SELLER
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return {
            "today_orders": today_orders_count,
            "today_sales": today_sales["total_sales"],
            "today_profit": today_profit["total_net_profit"],
            "month_sales": month_sales["total_sales"],
            "month_profit": month_profit["total_net_profit"],
            "owner_profit": month_profit["total_owner_profit"],
            "main_seller_profit": main_seller_commission,
            "contract_seller_profit": contract_seller_commission,
            "pending_payments": PaymentRepository.list_pending().count(),
            "low_stock_items": InventoryRepository.list_low_stock().count(),
        }

    @staticmethod
    def sales_trend(days=30):
        """Борлуулалтын тренд: өдөр тутмын нийт борлуулалт (сүүлийн N хоног).
        Зөвхөн Админ дуудна тул RBAC шүүлтгүйгээр бүх захиалгыг харна."""
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        orders = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=today,
        ).prefetch_related("items")

        daily_totals = {}
        for order in orders:
            day = timezone.localtime(order.created_at).date()
            for item in order.items.all():
                daily_totals[day] = daily_totals.get(day, Decimal("0")) + (
                    item.unit_price * item.quantity
                )

        return [
            {
                "date": start_date + timedelta(days=offset),
                "total": daily_totals.get(start_date + timedelta(days=offset), Decimal("0")),
            }
            for offset in range(days)
        ]

    @staticmethod
    def profit_trend(days=30):
        """Ашгийн тренд: өдөр тутмын нийт цэвэр ашиг (сүүлийн N хоног)."""
        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)

        orders = Order.objects.filter(
            status=OrderStatus.COMPLETED,
            created_at__date__gte=start_date,
            created_at__date__lte=today,
        ).prefetch_related("items__variant__product")

        daily_totals = {}
        for order in orders:
            day = timezone.localtime(order.created_at).date()
            for item in order.items.all():
                try:
                    breakdown = ProfitService.calculate_breakdown(item.variant.product)
                except БизнесАлдаа:
                    continue
                daily_totals[day] = daily_totals.get(day, Decimal("0")) + (
                    breakdown["net_profit"] * item.quantity
                )

        return [
            {
                "date": start_date + timedelta(days=offset),
                "total": daily_totals.get(start_date + timedelta(days=offset), Decimal("0")),
            }
            for offset in range(days)
        ]

    @staticmethod
    def province_report(start_date=None, end_date=None):
        """Аймгийн тайлан: дууссан захиалгуудыг Борлуулагчийн Аймгаар бүлэглэнэ."""
        start_date, end_date = resolve_date_range(start_date, end_date)
        orders = (
            Order.objects.filter(
                status=OrderStatus.COMPLETED,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date,
            )
            .select_related("seller")
            .prefetch_related("items")
        )

        provinces = {}
        for order in orders:
            province = order.seller.province or "Тодорхойгүй"
            entry = provinces.setdefault(
                province,
                {"province": province, "order_count": 0, "total_sales": Decimal("0")},
            )
            entry["order_count"] += 1
            for item in order.items.all():
                entry["total_sales"] += item.unit_price * item.quantity

        return sorted(provinces.values(), key=lambda row: row["total_sales"], reverse=True)
