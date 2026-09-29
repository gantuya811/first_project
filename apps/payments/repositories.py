"""
MERRIGE ERP - Төлбөрийн Repository
Repository Pattern: Database Logic зөвхөн энд байрлана.
"""

from django.db.models import Q

from apps.payments.models import Payment, PaymentStatus


class PaymentRepository:
    @staticmethod
    def get_by_uuid(payment_uuid):
        return Payment.objects.filter(uuid=payment_uuid).first()

    @staticmethod
    def list_for_order(order):
        return Payment.objects.filter(order=order).select_related("verified_by")

    @staticmethod
    def list_visible_to(user):
        """RBAC: Order.list_visible_to-той ижил шатлал."""
        if user.is_admin:
            return Payment.objects.all()
        if user.is_main_seller:
            return Payment.objects.filter(
                Q(order__seller_id=user.id) | Q(order__seller__parent_seller_id=user.id)
            )
        return Payment.objects.filter(order__seller_id=user.id)

    @staticmethod
    def get_visible_by_uuid(user, payment_uuid):
        return PaymentRepository.list_visible_to(user).filter(uuid=payment_uuid).first()

    @staticmethod
    def list_pending():
        return Payment.objects.filter(status=PaymentStatus.PENDING).select_related(
            "order", "order__seller"
        )
