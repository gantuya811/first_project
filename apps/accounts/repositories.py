"""
MERRIGE ERP - Хэрэглэгчийн Repository
Repository Pattern: Database Logic зөвхөн энд байрлана. Service Layer
шууд ORM queryset ашиглахгүй, энэ давхаргаар л дамжина.
"""

from django.db.models import Q

from apps.accounts.models import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def get_by_uuid(user_uuid):
        return User.objects.filter(uuid=user_uuid).first()

    @staticmethod
    def get_by_phone_number(phone_number):
        return User.objects.filter(phone_number=phone_number).first()

    @staticmethod
    def list_visible_to(requesting_user):
        """RBAC: Админ бүгдийг, Үндсэн Борлуулагч зөвхөн өөрийн Гэрээт
        Борлуулагчдыг (+өөрийгөө), Гэрээт Борлуулагч зөвхөн өөрийгөө харна."""
        if requesting_user.is_admin:
            return User.objects.all()
        if requesting_user.is_main_seller:
            return User.objects.filter(
                Q(id=requesting_user.id) | Q(parent_seller_id=requesting_user.id)
            )
        return User.objects.filter(id=requesting_user.id)

    @staticmethod
    def get_visible_by_uuid(requesting_user, target_uuid):
        return (
            UserRepository.list_visible_to(requesting_user)
            .filter(uuid=target_uuid)
            .first()
        )
