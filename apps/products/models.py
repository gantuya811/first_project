"""
MERRIGE ERP - Бараа бүтээгдэхүүний (Product) models
Бараа → Өнгө → Размер хослолоор Variant үүсэж, тухайн variant-ийн Үлдэгдэл
(агуулахын нөөц)-ийг STEP6-ийн apps.inventory app бүрэн эзэмшиж удирдана —
энд зөвхөн бүтцийг (аль Бараа, ямар Өнгө, ямар Размер) тодорхойлно.
apps.products нь apps.inventory-г огт мэдэхгүй байх ёстой (Modular
Monolith-ийн app хоорондын хамаарлыг зөв чиглэлд барих зарчим).

Код болон Барааны хувилбар (Product+Color+Size)-ын давхардлыг DB түвшинд
ч (Soft Delete-той нийцтэй нөхцөлт UniqueConstraint), Service Layer түвшинд
ч (Монгол алдааны мессежтэй) хоёуланг нь шалгаж хамгаална.
"""

from django.db import models

from apps.core.models import BaseModel
from apps.shared.validators import validate_image_extension, validate_image_size


class ProductStatus(models.TextChoices):
    DRAFT = "DRAFT", "Ноорог"
    ACTIVE = "ACTIVE", "Идэвхтэй"
    INACTIVE = "INACTIVE", "Идэвхгүй"


class ProductColor(models.TextChoices):
    BLACK = "BLACK", "Хар"
    WHITE = "WHITE", "Цагаан"
    BEIGE = "BEIGE", "Бэйж"
    GREEN = "GREEN", "Ногоон"
    PINK = "PINK", "Ягаан"
    RED = "RED", "Улаан"


class ProductSize(models.TextChoices):
    S = "S", "S"
    M = "M", "M"
    L = "L", "L"
    XL = "XL", "XL"
    XXL = "2XL", "2XL"
    XXXL = "3XL", "3XL"
    XXXXL = "4XL", "4XL"


def product_image_upload_path(instance, filename):
    return f"products/{instance.product.uuid}/{filename}"


def size_chart_upload_path(instance, filename):
    return f"products/{instance.uuid}/size_chart/{filename}"


class Product(BaseModel):
    code = models.CharField(verbose_name="Код", max_length=50)
    name = models.CharField(verbose_name="Нэр", max_length=255)
    description = models.TextField(verbose_name="Тайлбар", blank=True)
    material = models.CharField(
        verbose_name="Материалын мэдээлэл", max_length=255, blank=True
    )
    care_instructions = models.TextField(verbose_name="Арчилгааны заавар", blank=True)
    size_chart_image = models.ImageField(
        verbose_name="Размерийн хүснэгт",
        upload_to=size_chart_upload_path,
        validators=[validate_image_extension, validate_image_size],
        null=True,
        blank=True,
    )
    price = models.DecimalField(
        verbose_name="Үнэ (RRP)", max_digits=12, decimal_places=2
    )
    status = models.CharField(
        verbose_name="Төлөв",
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
    )

    class Meta:
        verbose_name = "Бараа"
        verbose_name_plural = "Бараа бүтээгдэхүүн"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(is_deleted=False),
                name="unique_active_product_code",
            )
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProductImage(BaseModel):
    MAX_IMAGES_PER_PRODUCT = 5

    product = models.ForeignKey(
        Product,
        verbose_name="Бараа",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        verbose_name="Зураг",
        upload_to=product_image_upload_path,
        validators=[validate_image_extension, validate_image_size],
    )
    is_primary = models.BooleanField(verbose_name="Үндсэн зураг эсэх", default=False)
    display_order = models.PositiveSmallIntegerField(
        verbose_name="Харагдах дараалал", default=0
    )

    class Meta:
        verbose_name = "Барааны зураг"
        verbose_name_plural = "Барааны зурагнууд"
        ordering = ["display_order", "created_at"]

    def __str__(self):
        return f"{self.product.code} - зураг {self.display_order}"


class ProductVariant(BaseModel):
    product = models.ForeignKey(
        Product,
        verbose_name="Бараа",
        on_delete=models.CASCADE,
        related_name="variants",
    )
    color = models.CharField(
        verbose_name="Өнгө", max_length=20, choices=ProductColor.choices
    )
    size = models.CharField(
        verbose_name="Размер", max_length=10, choices=ProductSize.choices
    )

    class Meta:
        verbose_name = "Барааны хувилбар"
        verbose_name_plural = "Барааны хувилбарууд"
        ordering = ["product", "color", "size"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "size"],
                condition=models.Q(is_deleted=False),
                name="unique_active_product_variant",
            )
        ]

    def __str__(self):
        return f"{self.product.code} / {self.get_color_display()} / {self.size}"
