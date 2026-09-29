"""
MERRIGE ERP - Агуулахын Repository
Repository Pattern: Database Logic зөвхөн энд байрлана. Service Layer
шууд ORM queryset ашиглахгүй, энэ давхаргаар л дамжина.
"""

from apps.inventory.models import InventoryMovement, Stock


class InventoryRepository:
    @staticmethod
    def get_stock_for_update(variant):
        """Зэрэгцээ (race condition) асуудлаас сэргийлж мөрийг түгжиж уншина
        (SELECT ... FOR UPDATE). Зөвхөн transaction.atomic() дотор дуудагдана.
        (Тэмдэглэл: SQLite орчинд бодит түгжээ хийгдэхгүй, зөвхөн PostgreSQL
        production орчинд бүрэн хамгаалалттай ажиллана.)"""
        return Stock.objects.select_for_update().select_related("variant").get(
            variant=variant
        )

    @staticmethod
    def get_stock_by_variant_uuid(variant_uuid):
        return (
            Stock.objects.filter(variant__uuid=variant_uuid)
            .select_related("variant", "variant__product")
            .first()
        )

    @staticmethod
    def list_stock():
        return Stock.objects.select_related("variant", "variant__product").all()

    @staticmethod
    def list_low_stock(threshold=5):
        return (
            Stock.objects.select_related("variant", "variant__product")
            .filter(quantity__lte=threshold)
            .order_by("quantity")
        )

    @staticmethod
    def list_movements(variant=None):
        queryset = InventoryMovement.objects.select_related(
            "variant", "variant__product", "created_by"
        ).all()
        if variant is not None:
            queryset = queryset.filter(variant=variant)
        return queryset
