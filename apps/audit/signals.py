"""
MERRIGE ERP - Audit Signals
Спецификейшнд заасан 6 ангиллыг (Нэвтрэлт, Захиалга, Төлбөр, Агуулах,
Тохиргоо, Хэрэглэгчийн өөрчлөлт) тухайн app-уудад АЛЬ ХЭДИЙН байгаа
модель/сигналууд дээр "сонсож" бүртгэнэ. apps.accounts, apps.orders,
apps.payments, apps.inventory, apps.profits нь apps.audit-ийн тухай юу ч
мэдэхгүй байх ёстой (STEP6/STEP10/STEP12-ийн загвартай адил зарчим).

Эх сурвалж бүрийн сонголтын шалтгаан:
- Нэвтрэлт: Django-ийн стандарт user_logged_in сигнал (IP хаягийг
  request-ээс шууд авах цорын ганц найдвартай цэг).
- Захиалга: OrderStatusHistory (аль хэдийн бүрэн бүтэцтэй, immutable).
- Агуулах: InventoryMovement (мөн адил).
- Тохиргоо: ProfitDistributionConfig (шинэ тохиргоо болгон created_by-тай).
- Төлбөр, Хэрэглэгч: Payment/User дээр өөрөө өөрчлөгддөг (in-place update)
  тул pre_save-ээр хуучин утгыг "тогтоож", post_save-ээр харьцуулна.
"""

from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.accounts.models import User
from apps.inventory.models import InventoryMovement
from apps.orders.models import OrderStatusHistory
from apps.payments.models import Payment
from apps.profits.models import ProfitDistributionConfig


def _client_ip_from_request(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ------------------------------------------------------------------
# 1. Нэвтрэлт
# ------------------------------------------------------------------
@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    AuditService.log(
        user=user,
        category=AuditCategory.LOGIN,
        action="Нэвтэрсэн",
        ip_address=_client_ip_from_request(request),
        object_reference=user.phone_number,
    )


# ------------------------------------------------------------------
# 2. Захиалга
# ------------------------------------------------------------------
@receiver(post_save, sender=OrderStatusHistory)
def audit_order_status_change(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    AuditService.log(
        user=instance.created_by,
        category=AuditCategory.ORDER,
        action=f"Захиалгын төлөв: {instance.from_status or '—'} → {instance.to_status}",
        object_reference=instance.order.order_number,
        old_value={"status": instance.from_status} if instance.from_status else None,
        new_value={"status": instance.to_status},
    )


# ------------------------------------------------------------------
# 3. Төлбөр
# ------------------------------------------------------------------
@receiver(pre_save, sender=Payment)
def _stash_old_payment_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._audit_old_status = Payment.objects.get(pk=instance.pk).status
        except Payment.DoesNotExist:
            instance._audit_old_status = None
    else:
        instance._audit_old_status = None


@receiver(post_save, sender=Payment)
def audit_payment_change(sender, instance, created, **kwargs):
    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    if created:
        AuditService.log(
            user=instance.created_by,
            category=AuditCategory.PAYMENT,
            action="Төлбөрийн баримт илгээсэн",
            object_reference=instance.order.order_number,
            new_value={"status": instance.status, "amount": str(instance.amount)},
        )
        return

    old_status = getattr(instance, "_audit_old_status", None)
    if old_status and old_status != instance.status:
        AuditService.log(
            user=instance.verified_by,
            category=AuditCategory.PAYMENT,
            action="Төлбөрийн төлөв өөрчлөгдсөн",
            object_reference=instance.order.order_number,
            old_value={"status": old_status},
            new_value={"status": instance.status},
        )


# ------------------------------------------------------------------
# 4. Агуулах
# ------------------------------------------------------------------
@receiver(post_save, sender=InventoryMovement)
def audit_inventory_movement(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    AuditService.log(
        user=instance.created_by,
        category=AuditCategory.INVENTORY,
        action=f"Агуулахын хөдөлгөөн: {instance.get_movement_type_display()}",
        object_reference=str(instance.variant),
        old_value={
            "quantity": instance.quantity_before,
            "reserved": instance.reserved_before,
        },
        new_value={
            "quantity": instance.quantity_after,
            "reserved": instance.reserved_after,
        },
    )


# ------------------------------------------------------------------
# 5. Тохиргоо
# ------------------------------------------------------------------
@receiver(post_save, sender=ProfitDistributionConfig)
def audit_settings_change(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    AuditService.log(
        user=instance.created_by,
        category=AuditCategory.SETTINGS,
        action="Ашиг хуваарилалтын тохиргоо өөрчлөгдсөн",
        new_value={
            "owner_percentage": str(instance.owner_percentage),
            "main_seller_percentage": str(instance.main_seller_percentage),
            "contract_seller_percentage": str(instance.contract_seller_percentage),
        },
    )


# ------------------------------------------------------------------
# 6. Хэрэглэгчийн өөрчлөлт
# ------------------------------------------------------------------
_TRACKED_USER_FIELDS = ["role", "is_approved", "is_active", "is_staff"]


@receiver(pre_save, sender=User)
def _stash_old_user_state(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = User.objects.get(pk=instance.pk)
            instance._audit_old_state = {
                field: getattr(old, field) for field in _TRACKED_USER_FIELDS
            }
        except User.DoesNotExist:
            instance._audit_old_state = None
    else:
        instance._audit_old_state = None


@receiver(post_save, sender=User)
def audit_user_change(sender, instance, created, **kwargs):
    if created:
        return  # Шинэ бүртгэл биш, зөвхөн дараагийн ӨӨРЧЛӨЛТИЙГ бүртгэнэ

    old_state = getattr(instance, "_audit_old_state", None)
    if not old_state:
        return

    new_state = {field: getattr(instance, field) for field in _TRACKED_USER_FIELDS}
    changed_fields = {
        field: (old_state[field], new_state[field])
        for field in _TRACKED_USER_FIELDS
        if old_state[field] != new_state[field]
    }
    if not changed_fields:
        return

    from apps.audit.models import AuditCategory
    from apps.audit.services import AuditService

    AuditService.log(
        user=instance.updated_by,
        category=AuditCategory.USER,
        action="Хэрэглэгчийн мэдээлэл өөрчлөгдсөн",
        object_reference=instance.phone_number,
        old_value={field: str(value[0]) for field, value in changed_fields.items()},
        new_value={field: str(value[1]) for field, value in changed_fields.items()},
    )
