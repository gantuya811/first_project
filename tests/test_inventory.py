"""
MERRIGE ERP - Inventory app-ийн тестүүд
"""

import pytest

from apps.inventory.models import InventoryMovement, MovementType
from apps.inventory.services import InventoryService
from apps.shared.exceptions import БизнесАлдаа

pytestmark = pytest.mark.django_db


# ------------------------------------------------------------------
# Unit Tests — models.py
# ------------------------------------------------------------------
class TestStockModel:
    def test_stock_auto_created_for_new_variant(self, variant, stock):
        assert stock.variant_id == variant.id
        assert stock.quantity == 0
        assert stock.reserved_quantity == 0

    def test_available_quantity_property(self, stock):
        stock.quantity = 10
        stock.reserved_quantity = 3
        assert stock.available_quantity == 7


class TestInventoryMovementImmutability:
    def test_cannot_update_movement(self, admin_user, stock, variant):
        InventoryService.stock_in(variant, 5, admin_user)
        movement = InventoryMovement.objects.first()
        movement.reason = "hacked"
        with pytest.raises(RuntimeError):
            movement.save()

    def test_cannot_delete_movement(self, admin_user, stock, variant):
        InventoryService.stock_in(variant, 5, admin_user)
        movement = InventoryMovement.objects.first()
        with pytest.raises(RuntimeError):
            movement.delete()


# ------------------------------------------------------------------
# Integration Tests — services.py
# ------------------------------------------------------------------
class TestInventoryService:
    def test_stock_in_increases_quantity(self, admin_user, variant, stock):
        updated = InventoryService.stock_in(variant, 10, admin_user, reason="орлого")
        assert updated.quantity == 10
        movement = InventoryMovement.objects.get(variant=variant)
        assert movement.movement_type == MovementType.STOCK_IN
        assert movement.quantity_before == 0
        assert movement.quantity_after == 10

    def test_stock_out_never_below_zero(self, admin_user, variant, stock):
        with pytest.raises(БизнесАлдаа):
            InventoryService.stock_out(variant, 1, admin_user)

    def test_stock_out_reduces_quantity_and_reserved(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 20, admin_user)
        InventoryService.reserve(variant, 5, admin_user)
        updated = InventoryService.stock_out(variant, 5, admin_user)
        assert updated.quantity == 15
        assert updated.reserved_quantity == 0

    def test_reserve_exceeding_available_raises(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        with pytest.raises(БизнесАлдаа):
            InventoryService.reserve(variant, 11, admin_user)

    def test_release_reservation_returns_availability(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        InventoryService.reserve(variant, 4, admin_user)
        updated = InventoryService.release_reservation(variant, 4, admin_user)
        assert updated.reserved_quantity == 0
        assert updated.available_quantity == 10

    def test_release_more_than_reserved_raises(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        InventoryService.reserve(variant, 3, admin_user)
        with pytest.raises(БизнесАлдаа):
            InventoryService.release_reservation(variant, 4, admin_user)

    def test_adjust_requires_reason(self, admin_user, variant, stock):
        with pytest.raises(БизнесАлдаа):
            InventoryService.adjust(variant, 5, admin_user, reason="")

    def test_adjust_below_reserved_raises(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        InventoryService.reserve(variant, 8, admin_user)
        with pytest.raises(БизнесАлдаа):
            InventoryService.adjust(variant, 5, admin_user, reason="тооллого")

    def test_adjust_creates_correct_delta(self, admin_user, variant, stock):
        InventoryService.stock_in(variant, 10, admin_user)
        updated = InventoryService.adjust(variant, 7, admin_user, reason="тооллогын зөрүү")
        assert updated.quantity == 7
        movement = InventoryMovement.objects.filter(
            variant=variant, movement_type=MovementType.ADJUSTMENT
        ).first()
        assert movement.quantity_change == -3


# ------------------------------------------------------------------
# API Tests
# ------------------------------------------------------------------
class TestInventoryAPI:
    def test_seller_can_view_stock(self, main_seller_client, stock):
        response = main_seller_client.get("/api/v1/inventory/stock/")
        assert response.status_code == 200
        assert response.data["data"]["count"] == 1

    def test_seller_cannot_stock_in(self, main_seller_client, variant):
        response = main_seller_client.post(
            f"/api/v1/inventory/stock/{variant.uuid}/stock-in/",
            {"quantity": 5},
            format="json",
        )
        assert response.status_code == 403

    def test_admin_stock_in_success(self, admin_client, variant):
        response = admin_client.post(
            f"/api/v1/inventory/stock/{variant.uuid}/stock-in/",
            {"quantity": 5, "reason": "орлого"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["data"]["quantity"] == 5

    def test_stock_out_insufficient_returns_mongolian_error(self, admin_client, variant, stock):
        response = admin_client.post(
            f"/api/v1/inventory/stock/{variant.uuid}/stock-out/",
            {"quantity": 100},
            format="json",
        )
        assert response.status_code == 400
        assert "хүрэлцэхгүй" in response.data["message"]
