"""
MERRIGE ERP - Ашгийн (Profit Engine) models
Хоёр гол загвар:
1. ProfitDistributionConfig — Ашиг хуваарилах хувь (Эзэн/Үндсэн/Гэрээт
   Борлуулагч), DATABASE-д хадгалагдана, hardcode ХИЙГДЭХГҮЙ. Шинэ
   тохиргоо үүсэх бүрд хуучныг идэвхгүй болгож, түүхийг бүрэн хадгална.
2. ProductCost — Барааны нууц зардлын бүтэц (Анхны үнэ, Тээвэр, Савлагаа,
   Шилжүүлгийн шимтгэл, Эрсдэлийн нөөц, Маркетинг, Нийлүүлэгчийн мэдээлэл).
   Эдгээр талбар бүгд "Зөвхөн Админ харна" гэсэн НУУЦ МЭДЭЭЛЭЛ.

Томьёо:
  Нийт зардал = Анхны үнэ + Тээвэр + Савлагаа + Шилжүүлгийн шимтгэл
                + Эрсдэлийн нөөц + Маркетинг
  Цэвэр ашиг  = RRP (Product.price) - Нийт зардал
"""

from decimal import Decimal

from django.db import models

from apps.core.models import BaseModel
from apps.products.models import Product


class ProfitDistributionConfig(BaseModel):
    """Ашиг хуваарилах идэвхтэй хувь. Гурван талбарын нийлбэр 100% байх
    ёстой. Систем даяар зөвхөн НЭГ идэвхтэй (is_active=True) мөр байна."""

    owner_percentage = models.DecimalField(
        verbose_name="Эзний хувь (%)", max_digits=5, decimal_places=2,
        default=Decimal("50.00"),
    )
    main_seller_percentage = models.DecimalField(
        verbose_name="Үндсэн Борлуулагчийн хувь (%)", max_digits=5, decimal_places=2,
        default=Decimal("20.00"),
    )
    contract_seller_percentage = models.DecimalField(
        verbose_name="Гэрээт Борлуулагчийн хувь (%)", max_digits=5, decimal_places=2,
        default=Decimal("30.00"),
    )
    is_active = models.BooleanField(verbose_name="Идэвхтэй эсэх", default=True)

    class Meta:
        verbose_name = "Ашиг хуваарилалтын тохиргоо"
        verbose_name_plural = "Ашиг хуваарилалтын тохиргоо"
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Эзэн {self.owner_percentage}% / Үндсэн {self.main_seller_percentage}% "
            f"/ Гэрээт {self.contract_seller_percentage}%"
        )


class ProductCost(BaseModel):
    """Барааны нууц зардлын бүтэц. Зөвхөн Админ харна (API-аар бусад
    хэрэглэгчид ил гарахгүй)."""

    product = models.OneToOneField(
        Product, verbose_name="Бараа", on_delete=models.CASCADE, related_name="cost"
    )
    original_price = models.DecimalField(
        verbose_name="Анхны үнэ", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    shipping_cost = models.DecimalField(
        verbose_name="Тээврийн зардал", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    packaging_cost = models.DecimalField(
        verbose_name="Савлагааны зардал", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    transfer_fee = models.DecimalField(
        verbose_name="Шилжүүлгийн шимтгэл", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    risk_reserve = models.DecimalField(
        verbose_name="Эрсдэлийн нөөц", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    marketing_cost = models.DecimalField(
        verbose_name="Маркетингийн зардал", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    supplier_info = models.CharField(
        verbose_name="Нийлүүлэгчийн мэдээлэл", max_length=255, blank=True
    )

    class Meta:
        verbose_name = "Барааны өртөг"
        verbose_name_plural = "Барааны өртгүүд"

    @property
    def total_cost(self):
        return (
            self.original_price
            + self.shipping_cost
            + self.packaging_cost
            + self.transfer_fee
            + self.risk_reserve
            + self.marketing_cost
        )

    @property
    def net_profit(self):
        return self.product.price - self.total_cost

    def __str__(self):
        return f"{self.product.code} - өртөг"
