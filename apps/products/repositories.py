"""
MERRIGE ERP - Барааны Repository
Repository Pattern: Database Logic зөвхөн энд байрлана. Service Layer
шууд ORM queryset ашиглахгүй, энэ давхаргаар л дамжина.
"""

from apps.products.models import Product, ProductImage, ProductVariant


class ProductRepository:
    @staticmethod
    def get_by_uuid(product_uuid):
        return Product.objects.filter(uuid=product_uuid).first()

    @staticmethod
    def get_by_code(code):
        return Product.objects.filter(code=code).first()

    @staticmethod
    def list_all():
        return Product.objects.all().prefetch_related("images", "variants")

    @staticmethod
    def count_images(product):
        return ProductImage.objects.filter(product=product).count()

    @staticmethod
    def variant_exists(product, color, size):
        return ProductVariant.objects.filter(
            product=product, color=color, size=size
        ).exists()
