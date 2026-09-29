"""
MERRIGE ERP - Хэрэглэгчийн (User) менежер
Стандарт Django-ийн username-ийн оронд утасны дугаараар хэрэглэгч
үүсгэх custom менежер. `createsuperuser` болон Service Layer-ийн
хэрэглэгч бүртгэх код эндээс дуудагдана.

BaseUserManager нь Core app-ын SoftDeleteManager-ийг өвлөхгүй тул
get_queryset()-ийг дарж бичиж, устгагдсан (is_deleted=True) хэрэглэгч
анхдагчаар харагдахгүй, улмаар нэвтэрч (authenticate) чадахгүй байхаар
нэгтгэсэн (Soft Delete Only дүрэм).
"""

from django.contrib.auth.base_user import BaseUserManager

from apps.core.managers import SoftDeleteQuerySet


class UserManager(BaseUserManager):
    use_in_migrations = True

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("Утасны дугаар заавал шаардлагатай.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.CONTRACT_SELLER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_approved", True)
        extra_fields.setdefault("must_change_password", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser хэрэглэгч is_staff=True байх ёстой.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser хэрэглэгч is_superuser=True байх ёстой.")

        return self._create_user(phone_number, password, **extra_fields)
