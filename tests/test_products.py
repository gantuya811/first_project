"""
MERRIGE ERP - Products app-ийн тестүүд
"""

from decimal import Decimal
from io import BytesIO

import pytest
from PIL import Image

from apps.products.models import Product, ProductImage, ProductVariant
from apps.products.services import ProductService
from apps.shared.exceptions import БизнесАлдаа, ДавхардсанБичлэгАлдаа

pytestmark = pytest.mark.django_db


def _make_image_file(name="test.jpg", fmt="JPEG"):
    buffer = BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format=fmt)
    buffer.seek(0)
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


# ------------------------------------------------------------------
# Unit Tests — models.py
# ------------------------------------------------------------------
class TestProductModel:
    def test_duplicate_active_code_blocked_at_db_level(self, product):
        with pytest.raises(Exception):
            Product.objects.create(code=product.code, name="Өөр нэр", price=Decimal("1"))

    def test_soft_deleted_code_can_be_reused(self, product):
        code = product.code
        product.delete()
        # Soft Delete-тэй нийцтэй нөхцөлт constraint тул дахин ашиглах боломжтой байх ёстой
        new_product = Product.objects.create(code=code, name="Шинэ бараа", price=Decimal("1"))
        assert new_product.code == code


# ------------------------------------------------------------------
# Integration Tests — services.py
# ------------------------------------------------------------------
class TestProductService:
    def test_create_product_duplicate_code_raises(self, product):
        with pytest.raises(ДавхардсанБичлэгАлдаа):
            ProductService.create_product(
                {"code": product.code, "name": "x", "price": Decimal("1")}
            )

    def test_add_variant_duplicate_combination_raises(self, product, variant):
        with pytest.raises(ДавхардсанБичлэгАлдаа):
            ProductService.add_variant(product, color=variant.color, size=variant.size)

    def test_add_image_enforces_max_five(self, product):
        for _ in range(ProductImage.MAX_IMAGES_PER_PRODUCT):
            ProductService.add_image(product, _make_image_file())
        with pytest.raises(БизнесАлдаа):
            ProductService.add_image(product, _make_image_file())

    def test_add_image_sets_only_one_primary(self, product):
        img1 = ProductService.add_image(product, _make_image_file("a.jpg"), is_primary=True)
        img2 = ProductService.add_image(product, _make_image_file("b.jpg"), is_primary=True)
        img1.refresh_from_db()
        assert img1.is_primary is False
        assert img2.is_primary is True


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestProductAPI:
    def test_anonymous_cannot_list_products(self, api_client):
        response = api_client.get("/api/v1/products/")
        assert response.status_code == 401

    def test_seller_can_list_products(self, main_seller_client, product):
        response = main_seller_client.get("/api/v1/products/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1

    def test_seller_cannot_create_product(self, main_seller_client):
        response = main_seller_client.post(
            "/api/v1/products/",
            {"code": "X1", "name": "X", "price": "1000"},
            format="json",
        )
        assert response.status_code == 403

    def test_admin_can_create_product(self, admin_client):
        response = admin_client.post(
            "/api/v1/products/",
            {"code": "NEW01", "name": "Шинэ бараа", "price": "5000.00"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["data"]["code"] == "NEW01"

    def test_admin_create_duplicate_code_returns_mongolian_error(self, admin_client, product):
        response = admin_client.post(
            "/api/v1/products/",
            {"code": product.code, "name": "Х", "price": "1000"},
            format="json",
        )
        assert response.status_code == 400
        assert "бүртгэлтэй" in str(response.data["errors"])

    def test_admin_create_negative_price_rejected(self, admin_client):
        response = admin_client.post(
            "/api/v1/products/",
            {"code": "NEG01", "name": "Х", "price": "-100"},
            format="json",
        )
        assert response.status_code == 400

    def test_image_upload_rejects_non_image_extension(self, admin_client, product):
        from django.core.files.uploadedfile import SimpleUploadedFile

        fake_file = SimpleUploadedFile("virus.exe", b"not an image", content_type="application/octet-stream")
        response = admin_client.post(
            f"/api/v1/products/{product.uuid}/images/",
            {"image": fake_file},
            format="multipart",
        )
        assert response.status_code == 400

    def test_image_upload_accepts_valid_jpg(self, admin_client, product):
        response = admin_client.post(
            f"/api/v1/products/{product.uuid}/images/",
            {"image": _make_image_file()},
            format="multipart",
        )
        assert response.status_code == 201

    def test_variant_create_invalid_color_rejected(self, admin_client, product):
        response = admin_client.post(
            f"/api/v1/products/{product.uuid}/variants/",
            {"color": "PURPLE", "size": "M"},
            format="json",
        )
        assert response.status_code == 400
