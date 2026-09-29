"""
MERRIGE ERP - Барааны Service Layer
Бизнесийн дүрмүүд (барааны код давхардахгүй, нэг бараанд хамгийн ихдээ
5 зураг, өнгө+размерийн хослол давхардахгүй) зөвхөн энд байрлана.
"""

from apps.products.models import Product, ProductImage, ProductVariant
from apps.products.repositories import ProductRepository
from apps.shared.exceptions import БизнесАлдаа, ДавхардсанБичлэгАлдаа


class ProductService:
    @staticmethod
    def create_product(data):
        if ProductRepository.get_by_code(data["code"]) is not None:
            raise ДавхардсанБичлэгАлдаа("Энэ барааны код бүртгэлтэй байна.")
        return Product.objects.create(**data)

    @staticmethod
    def update_product(product, data):
        new_code = data.get("code")
        if new_code and new_code != product.code:
            existing = ProductRepository.get_by_code(new_code)
            if existing is not None and existing.id != product.id:
                raise ДавхардсанБичлэгАлдаа("Энэ барааны код бүртгэлтэй байна.")

        for field, value in data.items():
            setattr(product, field, value)
        product.save()
        return product

    @staticmethod
    def delete_product(product):
        product.delete()  # Soft Delete Only

    @staticmethod
    def add_image(product, image_file, is_primary=False):
        current_count = ProductRepository.count_images(product)
        if current_count >= ProductImage.MAX_IMAGES_PER_PRODUCT:
            raise БизнесАлдаа(
                f"Нэг бараанд хамгийн ихдээ {ProductImage.MAX_IMAGES_PER_PRODUCT} "
                "зураг оруулах боломжтой."
            )

        if is_primary:
            ProductImage.objects.filter(product=product, is_primary=True).update(
                is_primary=False
            )

        return ProductImage.objects.create(
            product=product,
            image=image_file,
            is_primary=is_primary,
            display_order=current_count,
        )

    @staticmethod
    def delete_image(image):
        image.delete()  # Soft Delete Only

    @staticmethod
    def add_variant(product, color, size):
        if ProductRepository.variant_exists(product, color, size):
            raise ДавхардсанБичлэгАлдаа(
                "Энэ бараанд ийм өнгө, размерийн хослол аль хэдийн бүртгэлтэй байна."
            )
        return ProductVariant.objects.create(product=product, color=color, size=size)

    @staticmethod
    def delete_variant(variant):
        variant.delete()  # Soft Delete Only
