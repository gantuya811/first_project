"""
MERRIGE ERP - Шимтгэлийн Repository
Repository Pattern: Database Logic зөвхөн энд байрлана.
"""

from django.db.models import Q

from apps.commissions.models import Commission


class CommissionRepository:
    @staticmethod
    def get_by_uuid(commission_uuid):
        return Commission.objects.filter(uuid=commission_uuid).first()

    @staticmethod
    def exists_for_order(order):
        return Commission.objects.filter(order=order).exists()

    @staticmethod
    def list_visible_to(user):
        """RBAC: Order/Payment-тэй ижил гурван шатлал."""
        if user.is_admin:
            return Commission.objects.all()
        if user.is_main_seller:
            return Commission.objects.filter(
                Q(seller_id=user.id) | Q(seller__parent_seller_id=user.id)
            )
        return Commission.objects.filter(seller_id=user.id)

    @staticmethod
    def get_visible_by_uuid(user, commission_uuid):
        return (
            CommissionRepository.list_visible_to(user)
            .filter(uuid=commission_uuid)
            .first()
        )
