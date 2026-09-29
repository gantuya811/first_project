"""
MERRIGE ERP - Inventory Signals
Шинэ ProductVariant үүсэх бүрд харгалзах Stock (үлдэгдэл, эхлээд 0) мөрийг
автоматаар үүсгэнэ. Хамаарлыг зөв чиглэлд (inventory → products) барихын
тулд apps.products нь apps.inventory-ийн тухай юу ч мэдэхгүй байна.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.inventory.models import Stock
from apps.products.models import ProductVariant


@receiver(post_save, sender=ProductVariant)
def create_stock_for_new_variant(sender, instance, created, **kwargs):
    if created:
        Stock.objects.get_or_create(variant=instance)
