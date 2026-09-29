"""
MERRIGE ERP - Барааны Django Admin тохиргоо
100% Монгол хэл дээрх талбар, гарчиг, бүлэглэлттэй админ панель.
"""

from django.contrib import admin

from apps.products.models import Product, ProductImage, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "is_primary", "display_order")
    verbose_name = "Зураг"
    verbose_name_plural = "Зурагнууд (хамгийн ихдээ 5)"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ("color", "size")
    verbose_name = "Хувилбар"
    verbose_name_plural = (
        "Өнгө, Размерийн хувилбарууд "
        "(Үлдэгдэл/quantity-г Агуулах (Inventory) хэсгээс тохируулна)"
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("code", "name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [ProductImageInline, ProductVariantInline]

    fieldsets = (
        ("Үндсэн мэдээлэл", {"fields": ("code", "name", "description", "status")}),
        (
            "Материал, арчилгаа",
            {"fields": ("material", "care_instructions", "size_chart_image")},
        ),
        ("Үнэ", {"fields": ("price",)}),
        ("Огноо", {"fields": ("uuid", "created_at", "updated_at")}),
    )
