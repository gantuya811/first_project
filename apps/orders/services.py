"""
MERRIGE ERP - Захиалгын Service Layer
Төлөв шилжилтийн бүх дүрэм (аль төлөвөөс аль төлөв рүү шилжиж болох),
Агуулахтай (Inventory) интеграц (батлагдахад нөөцлөх, цуцлахад чөлөөлөх,
илгээхэд зарлагадах) зөвхөн энд байрлана. Төлөв бүрийн шилжилт
OrderStatusHistory-д өөрчлөгдөшгүй бичигдэнэ.
"""

from django.db import transaction
from django.utils import timezone

from apps.inventory.services import InventoryService
from apps.orders.models import GroupedOrder, Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.products.models import ProductVariant
from apps.shared.exceptions import БизнесАлдаа

# Төлөв бүрээс аль төлөв рүү шилжиж болохыг тодорхойлсон зөвшөөрөгдсөн
# шилжилтийн газрын зураг (Finite State Machine).
TRANSITIONS = {
    OrderStatus.REQUESTED: {OrderStatus.UNDER_REVIEW, OrderStatus.CANCELLED},
    OrderStatus.UNDER_REVIEW: {
        OrderStatus.APPROVED,
        OrderStatus.REJECTED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.APPROVED: {OrderStatus.PAYMENT_PENDING, OrderStatus.CANCELLED},
    OrderStatus.PAYMENT_PENDING: {OrderStatus.PAYMENT_REVIEW, OrderStatus.CANCELLED},
    OrderStatus.PAYMENT_REVIEW: {
        OrderStatus.PAYMENT_CONFIRMED,
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAYMENT_CONFIRMED: {OrderStatus.GROUPED_ORDER, OrderStatus.CANCELLED},
    OrderStatus.GROUPED_ORDER: {OrderStatus.ARRIVED},
    OrderStatus.ARRIVED: {OrderStatus.SHIPPING},
    OrderStatus.SHIPPING: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.REJECTED: set(),
    OrderStatus.CANCELLED: set(),
}

# Захиалга нөөцлөгдсөн байж болох (цуцлах үед агуулах чөлөөлөх шаардлагатай) төлөвүүд.
_RESERVED_STATUSES = {
    OrderStatus.APPROVED,
    OrderStatus.PAYMENT_PENDING,
    OrderStatus.PAYMENT_REVIEW,
    OrderStatus.PAYMENT_CONFIRMED,
}


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(seller, items_data, note=""):
        """Борлуулагч захиалгын хүсэлт илгээнэ (REQUESTED)."""
        if not items_data:
            raise БизнесАлдаа("Захиалгад хамгийн багадаа нэг бараа байх ёстой.")

        order = Order.objects.create(
            order_number=OrderService._generate_order_number(),
            seller=seller,
            status=OrderStatus.REQUESTED,
            note=note,
        )
        for item in items_data:
            variant = ProductVariant.objects.filter(
                uuid=item["variant_uuid"]
            ).first()
            if variant is None:
                raise БизнесАлдаа(
                    f"Барааны хувилбар олдсонгүй: {item['variant_uuid']}"
                )
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=item["quantity"],
                unit_price=variant.product.price,
            )

        OrderService._log_history(
            order, "", OrderStatus.REQUESTED, seller, "Захиалга үүсгэв"
        )
        return order

    @staticmethod
    @transaction.atomic
    def start_review(order, user):
        """Админ захиалгыг хянаж эхэлнэ."""
        return OrderService.transition_status(order, OrderStatus.UNDER_REVIEW, user)

    @staticmethod
    @transaction.atomic
    def approve(order, user):
        """Админ 'Боломжтой' гэж шийднэ: батлаад, агуулахаас нөөцөлж,
        төлбөр хүлээх төлөвт шилжинэ."""
        order = OrderService.transition_status(order, OrderStatus.APPROVED, user)

        for item in order.items.select_related("variant"):
            InventoryService.reserve(
                item.variant, item.quantity, user, reference=order.order_number
            )

        return OrderService.transition_status(
            order,
            OrderStatus.PAYMENT_PENDING,
            user,
            reason="Захиалга батлагдаж, төлбөр хүлээгдэж буй төлөвт шилжлээ.",
        )

    @staticmethod
    @transaction.atomic
    def reject(order, user, reason):
        """Админ 'Боломжгүй' гэж шийднэ."""
        if not reason:
            raise БизнесАлдаа("Татгалзах шалтгаанаа заавал бичнэ үү.")

        order = OrderService.transition_status(
            order, OrderStatus.REJECTED, user, reason
        )
        order.rejected_reason = reason
        order.save(update_fields=["rejected_reason"])
        return order

    @staticmethod
    @transaction.atomic
    def cancel(order, user, reason):
        """Борлуулагч (өөрийн) эсвэл Админ захиалгыг цуцална. Нөөцлөгдсөн
        байсан бол агуулахыг чөлөөлнө."""
        if not reason:
            raise БизнесАлдаа("Цуцлах шалтгаанаа заавал бичнэ үү.")

        was_reserved = order.status in _RESERVED_STATUSES

        order = OrderService.transition_status(
            order, OrderStatus.CANCELLED, user, reason
        )
        order.cancelled_reason = reason
        order.save(update_fields=["cancelled_reason"])

        if was_reserved:
            for item in order.items.select_related("variant"):
                InventoryService.release_reservation(
                    item.variant, item.quantity, user, reference=order.order_number
                )

        return order

    @staticmethod
    @transaction.atomic
    def group(order, grouped_order, user):
        """Төлбөр баталгаажсан захиалгыг Нэгдсэн захиалганд оруулна."""
        order.grouped_order = grouped_order
        order.save(update_fields=["grouped_order"])
        return OrderService.transition_status(
            order,
            OrderStatus.GROUPED_ORDER,
            user,
            reason=f"Нэгдсэн захиалга: {grouped_order.order_number}",
        )

    @staticmethod
    @transaction.atomic
    def mark_arrived(order, user):
        """Нэгдсэн захиалгаар авсан бараа агуулахад ирнэ."""
        return OrderService.transition_status(order, OrderStatus.ARRIVED, user)

    @staticmethod
    @transaction.atomic
    def ship(order, user):
        """Бараа хүргэлтэд гарна — агуулахаас бодитоор зарлагадана."""
        order = OrderService.transition_status(order, OrderStatus.SHIPPING, user)

        for item in order.items.select_related("variant"):
            InventoryService.stock_out(
                item.variant,
                item.quantity,
                user,
                reason="Захиалга хүргэлтэд гарлаа",
                reference=order.order_number,
            )

        return order

    @staticmethod
    @transaction.atomic
    def complete(order, user):
        """Захиалга дуусна (Шимтгэл энэ төлөвөөс хойш бодогдоно, STEP10)."""
        return OrderService.transition_status(order, OrderStatus.COMPLETED, user)

    @staticmethod
    def transition_status(order, new_status, user, reason=""):
        """Ерөнхий (дараагийн STEP-үүд, тухайлбал Payments, дуудаж болох)
        төлөв шилжилтийн цөм механизм. TRANSITIONS-д зөвшөөрөгдөөгүй
        шилжилтийг хориглоно."""
        allowed = TRANSITIONS.get(order.status, set())
        if new_status not in allowed:
            raise БизнесАлдаа(
                f"'{order.get_status_display()}' төлөвөөс "
                f"'{OrderStatus(new_status).label}' төлөв рүү шилжих боломжгүй."
            )

        old_status = order.status
        order.status = new_status
        order.save(update_fields=["status"])
        OrderService._log_history(order, old_status, new_status, user, reason)
        return order

    @staticmethod
    def _log_history(order, from_status, to_status, user, reason=""):
        OrderStatusHistory.objects.create(
            order=order,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            created_by=user,
        )

    @staticmethod
    def _generate_order_number():
        prefix = f"ORD-{timezone.now():%Y%m%d}-"
        last = (
            Order.all_objects.filter(order_number__startswith=prefix)
            .order_by("-order_number")
            .first()
        )
        next_seq = 1 if last is None else int(last.order_number.replace(prefix, "")) + 1
        return f"{prefix}{next_seq:05d}"


class GroupedOrderService:
    @staticmethod
    @transaction.atomic
    def create(user, note=""):
        grouped_order = GroupedOrder.objects.create(
            order_number=GroupedOrderService._generate_order_number(),
            note=note,
            created_by=user,
        )
        return grouped_order

    @staticmethod
    def _generate_order_number():
        prefix = f"GO-{timezone.now():%Y%m}-"
        last = (
            GroupedOrder.all_objects.filter(order_number__startswith=prefix)
            .order_by("-order_number")
            .first()
        )
        next_seq = 1 if last is None else int(last.order_number.replace(prefix, "")) + 1
        return f"{prefix}{next_seq:05d}"
