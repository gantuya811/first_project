"""
MERRIGE ERP - Захиалгын Repository
Repository Pattern: Database Logic зөвхөн энд байрлана.
"""

from django.db.models import Q

from apps.orders.models import GroupedOrder, Order


class OrderRepository:
    @staticmethod
    def get_by_uuid(order_uuid):
        return Order.objects.filter(uuid=order_uuid).first()

    @staticmethod
    def list_visible_to(user):
        """RBAC: Админ бүгдийг, Үндсэн Борлуулагч өөрийн болон өөрийн
        Гэрээт Борлуулагчдын захиалгыг, Гэрээт Борлуулагч зөвхөн өөрийн
        захиалгыг харна."""
        if user.is_admin:
            return Order.objects.all()
        if user.is_main_seller:
            return Order.objects.filter(
                Q(seller_id=user.id) | Q(seller__parent_seller_id=user.id)
            )
        return Order.objects.filter(seller_id=user.id)

    @staticmethod
    def get_visible_by_uuid(user, order_uuid):
        return OrderRepository.list_visible_to(user).filter(uuid=order_uuid).first()


class GroupedOrderRepository:
    @staticmethod
    def get_by_uuid(grouped_order_uuid):
        return GroupedOrder.objects.filter(uuid=grouped_order_uuid).first()

    @staticmethod
    def list_all():
        return GroupedOrder.objects.all()
