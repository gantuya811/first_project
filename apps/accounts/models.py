"""
MERRIGE ERP - Custom User Model
Утасны дугаараар нэвтэрдэг, гурван шатлалт эрхтэй (Админ, Үндсэн Борлуулагч,
Гэрээт Борлуулагч) хэрэглэгчийн загвар.

Дүрэм:
- Username = phone_number
- Гэрээт Борлуулагч заавал нэг Үндсэн Борлуулагчид (parent_seller) харьяалагдана
- Үндсэн болон Гэрээт Борлуулагч Админ баталгаажуулсны дараа идэвхжинэ
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import BaseModel
from apps.shared.validators import validate_phone_number


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Админ"
        MAIN_SELLER = "MAIN_SELLER", "Үндсэн Борлуулагч"
        CONTRACT_SELLER = "CONTRACT_SELLER", "Гэрээт Борлуулагч"

    # --- Нэвтрэлтийн мэдээлэл ---
    phone_number = models.CharField(
        verbose_name="Утасны дугаар",
        max_length=8,
        unique=True,
        validators=[validate_phone_number],
        help_text="Нэвтрэх нэрээр ашиглагдана. 8 оронтой байна.",
    )
    email = models.EmailField(verbose_name="И-мэйл хаяг", unique=True)

    # --- Хувийн мэдээлэл ---
    last_name = models.CharField(verbose_name="Овог", max_length=150)
    first_name = models.CharField(verbose_name="Нэр", max_length=150)

    # --- Эрх, шатлал ---
    role = models.CharField(
        verbose_name="Хэрэглэгчийн төрөл",
        max_length=20,
        choices=Role.choices,
        default=Role.CONTRACT_SELLER,
    )
    parent_seller = models.ForeignKey(
        "self",
        verbose_name="Харьяалагдах үндсэн борлуулагч",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contract_sellers",
        limit_choices_to={"role": Role.MAIN_SELLER},
        help_text="Гэрээт борлуулагч заавал энэ талбараар нэг үндсэн борлуулагчид харьяалагдана.",
    )

    # --- Дэлгүүр, хаягийн мэдээлэл ---
    store_name = models.CharField(verbose_name="Дэлгүүрийн нэр", max_length=255, blank=True)
    province = models.CharField(verbose_name="Аймаг", max_length=100, blank=True)
    soum = models.CharField(verbose_name="Сум", max_length=100, blank=True)
    district = models.CharField(verbose_name="Дүүрэг", max_length=100, blank=True)
    address = models.TextField(verbose_name="Хаяг", blank=True)

    # --- Банкны мэдээлэл ---
    bank_name = models.CharField(verbose_name="Банкны нэр", max_length=100, blank=True)
    account_number = models.CharField(verbose_name="Дансны дугаар", max_length=50, blank=True)

    # --- Баталгаажуулалт, төлөв ---
    is_approved = models.BooleanField(verbose_name="Админ баталгаажуулсан эсэх", default=False)
    approved_by = models.ForeignKey(
        "self",
        verbose_name="Баталгаажуулсан админ",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_users",
        limit_choices_to={"role": Role.ADMIN},
    )
    approved_at = models.DateTimeField(verbose_name="Баталгаажуулсан огноо", null=True, blank=True)
    must_change_password = models.BooleanField(
        verbose_name="Нэвтрэхэд нууц үг заавал солих эсэх", default=True
    )
    is_active = models.BooleanField(verbose_name="Идэвхтэй эсэх", default=True)
    is_staff = models.BooleanField(
        verbose_name="Django Admin-д нэвтрэх эрхтэй эсэх", default=False
    )

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    class Meta:
        verbose_name = "Хэрэглэгч"
        verbose_name_plural = "Хэрэглэгчид"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name}".strip()

    def get_short_name(self):
        return self.first_name

    def clean(self):
        super().clean()
        if self.role == self.Role.CONTRACT_SELLER and self.parent_seller_id is None:
            raise ValidationError(
                {
                    "parent_seller": "Гэрээт борлуулагч заавал нэг үндсэн "
                    "борлуулагчид харьяалагдах ёстой."
                }
            )
        if self.role != self.Role.CONTRACT_SELLER and self.parent_seller_id is not None:
            raise ValidationError(
                {
                    "parent_seller": "Зөвхөн Гэрээт Борлуулагч төрлийн хэрэглэгч "
                    "харьяалагдах үндсэн борлуулагчтай байж болно."
                }
            )

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_main_seller(self):
        return self.role == self.Role.MAIN_SELLER

    @property
    def is_contract_seller(self):
        return self.role == self.Role.CONTRACT_SELLER
