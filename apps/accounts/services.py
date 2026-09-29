"""
MERRIGE ERP - Accounts Service Layer
Нэвтрэлт, хэрэглэгч бүртгэх/баталгаажуулах зэрэг бизнесийн БҮХ дүрмийг
эндээс удирдана. View/Serializer шууд Repository-оос гадуур өгөгдөл
авахгүй, JWT-ийг ч энэ давхаргаас гаргана (Clean Architecture / Service
Layer дүрэм).
"""

from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.repositories import UserRepository
from apps.accounts.utils import generate_random_password
from apps.shared.exceptions import БизнесАлдаа


class AuthService:
    @staticmethod
    def authenticate(phone_number, password):
        """Утасны дугаар, нууц үгээр нэвтрэлтийг баталгаажуулна.

        Тэмдэглэл: Баталгаажаагүй (is_approved=False) хэрэглэгч бүртгэлийн
        үед "ашиглах боломжгүй" (unusable) нууц үгтэй үүсдэг тул
        check_password() шалгалтаас ӨМНӨ is_approved-ийг шалгаж, тодорхой
        "баталгаажаагүй" мессежийг харуулна.
        """
        user = UserRepository.get_by_phone_number(phone_number)

        if user is None:
            raise БизнесАлдаа("Утасны дугаар эсвэл нууц үг буруу байна.")

        if not user.is_admin and not user.is_approved:
            raise БизнесАлдаа(
                "Таны бүртгэлийг Админ баталгаажуулаагүй тул нэвтрэх боломжгүй байна."
            )

        if not user.check_password(password):
            raise БизнесАлдаа("Утасны дугаар эсвэл нууц үг буруу байна.")

        if not user.is_active:
            raise БизнесАлдаа("Таны эрх түдгэлзүүлэгдсэн байна. Админтай холбогдоно уу.")

        return user

    @staticmethod
    def issue_tokens(user, request=None):
        """Нэвтэрсэн хэрэглэгчид зориулсан JWT access/refresh токен үүсгэнэ.

        Django-ийн стандарт `user_logged_in` сигналыг илгээснээр:
        1) SimpleJWT-ийн UPDATE_LAST_LOGIN тохиргоо ажиллаж, last_login
           талбар шинэчлэгдэнэ (өмнө нь сигнал огт илгээгддэггүй байсан
           тул last_login хэзээ ч шинэчлэгддэггүй байсан бага зэргийн
           алдааг эндээс дагаж заслаа);
        2) apps.audit STEP13-т энэ сигналыг сонсож "Нэвтрэлт" ангиллын
           аудит лог (IP хаягийн хамт) үүсгэнэ, apps.accounts нь
           apps.audit-ийн тухай юу ч мэдэхгүй хэвээр байна.
        """
        refresh = RefreshToken.for_user(user)
        user_logged_in.send(sender=user.__class__, request=request, user=user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    @staticmethod
    def change_password(user, new_password):
        """Нууц үг солиод, эхний-нэвтрэлтийн хориг (must_change_password)-г цуцална."""
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])


class UserService:
    @staticmethod
    def register(validated_data):
        """Шинэ Үндсэн/Гэрээт Борлуулагч бүртгэнэ.

        Дүрэм: Гэрээт Борлуулагч заавал баталгаажсан Үндсэн Борлуулагчийн
        утасны дугаараар "Таныг бүртгүүлсэн үндсэн борлуулагч"-аа зааж өгнө.
        Бүртгэл шууд идэвхжихгүй (is_approved=False), Админ баталгаажуулах
        хүртэл нэвтрэх боломжгүй, тул "ашиглах боломжгүй" нууц үгтэй үүснэ.
        """
        data = dict(validated_data)
        parent_seller_phone = data.pop("parent_seller_phone", "") or ""
        role = data["role"]

        parent_seller = None
        if role == User.Role.CONTRACT_SELLER:
            parent_seller = UserRepository.get_by_phone_number(parent_seller_phone)
            if (
                parent_seller is None
                or not parent_seller.is_main_seller
                or not parent_seller.is_approved
            ):
                raise БизнесАлдаа(
                    "Тухайн утасны дугаартай баталгаажсан Үндсэн Борлуулагч олдсонгүй."
                )

        user = User(parent_seller=parent_seller, **data)
        user.set_unusable_password()
        user.save()
        return user

    @staticmethod
    def list_visible(requesting_user):
        return UserRepository.list_visible_to(requesting_user)

    @staticmethod
    def get_visible(requesting_user, target_uuid):
        user = UserRepository.get_visible_by_uuid(requesting_user, target_uuid)
        if user is None:
            raise NotFound()
        return user

    @staticmethod
    def approve(target_uuid, approved_by):
        """Админ хэрэглэгчийг баталгаажуулж, санамсаргүй анхны нууц үг олгоно."""
        user = UserRepository.get_by_uuid(target_uuid)
        if user is None:
            raise NotFound()

        if user.is_approved:
            raise БизнесАлдаа("Энэ хэрэглэгч аль хэдийн баталгаажсан байна.")

        random_password = generate_random_password()
        user.set_password(random_password)
        user.is_approved = True
        user.approved_by = approved_by
        user.approved_at = timezone.now()
        user.updated_by = approved_by
        user.save(
            update_fields=[
                "password",
                "is_approved",
                "approved_by",
                "approved_at",
                "updated_by",
            ]
        )
        return user, random_password

    @staticmethod
    def deactivate(target_uuid, actor=None):
        """Хэрэглэгчийг идэвхгүй болгоно (Soft Delete Only дүрмийн дагуу)."""
        user = UserRepository.get_by_uuid(target_uuid)
        if user is None:
            raise NotFound()
        if actor is not None:
            user.updated_by = actor
            user.save(update_fields=["updated_by"])
        user.delete()
        return user
