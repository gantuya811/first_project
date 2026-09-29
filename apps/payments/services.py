"""
MERRIGE ERP - Төлбөрийн Service Layer
Захиалгын Service Layer-тэй (apps.orders.services.OrderService) интеграцтай
ажиллана: баримт илгээхэд захиалга PAYMENT_REVIEW рүү, баталгаажуулахад
PAYMENT_CONFIRMED рүү, татгалзахад дахин PAYMENT_PENDING рүү шилжинэ.
"""

from django.db import transaction
from django.utils import timezone

from apps.orders.models import OrderStatus
from apps.orders.services import OrderService
from apps.payments.models import Payment, PaymentStatus
from apps.shared.exceptions import БизнесАлдаа, ЭрхийнАлдаа


class PaymentService:
    @staticmethod
    @transaction.atomic
    def submit_payment(order, seller, receipt_file, amount):
        """Борлуулагч төлбөрийн баримт илгээнэ. Зөвхөн PAYMENT_PENDING
        төлөвтэй, өөрийн захиалгад л боломжтой."""
        if order.seller_id != seller.id:
            raise ЭрхийнАлдаа(
                "Зөвхөн өөрийн захиалгад төлбөрийн баримт оруулах боломжтой."
            )
        if order.status != OrderStatus.PAYMENT_PENDING:
            raise БизнесАлдаа(
                f"'{order.get_status_display()}' төлөвтэй захиалгад "
                "төлбөрийн баримт оруулах боломжгүй."
            )

        payment = Payment.objects.create(
            order=order,
            receipt_file=receipt_file,
            amount=amount,
            status=PaymentStatus.PENDING,
            created_by=seller,
        )

        OrderService.transition_status(
            order,
            OrderStatus.PAYMENT_REVIEW,
            seller,
            reason="Төлбөрийн баримт хүлээн авав, шалгагдаж байна.",
        )
        return payment

    @staticmethod
    @transaction.atomic
    def confirm(payment, admin_user):
        """Админ гараар шалгаж баталгаажуулна. Нэг төлбөрийг дахин
        баталгаажуулах боломжгүй."""
        if payment.status != PaymentStatus.PENDING:
            raise БизнесАлдаа("Энэ төлбөрийг дахин баталгаажуулах боломжгүй.")

        payment.status = PaymentStatus.CONFIRMED
        payment.verified_by = admin_user
        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "verified_by", "verified_at"])

        OrderService.transition_status(
            payment.order,
            OrderStatus.PAYMENT_CONFIRMED,
            admin_user,
            reason="Төлбөр баталгаажлаа.",
        )
        return payment

    @staticmethod
    @transaction.atomic
    def reject(payment, admin_user, reason):
        """Админ татгалзана — захиалга дахин баримт оруулах боломжтой
        PAYMENT_PENDING төлөвт буцна."""
        if payment.status != PaymentStatus.PENDING:
            raise БизнесАлдаа("Энэ төлбөрийн шийдвэрийг өөрчлөх боломжгүй.")
        if not reason:
            raise БизнесАлдаа("Татгалзах шалтгаанаа заавал бичнэ үү.")

        payment.status = PaymentStatus.REJECTED
        payment.rejected_reason = reason
        payment.verified_by = admin_user
        payment.verified_at = timezone.now()
        payment.save(
            update_fields=["status", "rejected_reason", "verified_by", "verified_at"]
        )

        OrderService.transition_status(
            payment.order,
            OrderStatus.PAYMENT_PENDING,
            admin_user,
            reason=f"Төлбөр татгалзагдлаа: {reason}",
        )
        return payment
