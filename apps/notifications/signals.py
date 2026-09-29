"""
MERRIGE ERP - Notification Signals
Захиалгын төлөв өөрчлөгдөх (батлагдах, татгалзагдах, төлбөр
баталгаажих, бараа ирэх, хүргэлт эхлэх) болон шимтгэл бодогдох үед
холбогдох Борлуулагчид мэдэгдэл автоматаар илгээнэ. apps.orders,
apps.commissions нь apps.notifications-ийн тухай юу ч мэдэхгүй байх
ёстой тул хамаарлыг зөв чиглэлд (notifications → orders/commissions)
signal-аар холбоно (STEP6/STEP10-ийн загвартай адил).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.commissions.models import Commission
from apps.orders.models import OrderStatus, OrderStatusHistory

# to_status -> (notification_type, гарчиг, мессежийн загвар)
_ORDER_STATUS_NOTIFICATIONS = {
    OrderStatus.APPROVED: (
        "ORDER_APPROVED",
        "Захиалга батлагдлаа",
        "Таны {order_number} дугаартай захиалга батлагдлаа.",
    ),
    OrderStatus.REJECTED: (
        "ORDER_REJECTED",
        "Захиалга татгалзагдлаа",
        "Таны {order_number} дугаартай захиалга татгалзагдлаа.",
    ),
    OrderStatus.PAYMENT_CONFIRMED: (
        "PAYMENT_CONFIRMED",
        "Төлбөр батлагдлаа",
        "Таны {order_number} дугаартай захиалгын төлбөр баталгаажлаа.",
    ),
    OrderStatus.ARRIVED: (
        "STOCK_ARRIVED",
        "Бараа ирлээ",
        "Таны {order_number} дугаартай захиалгын бараа агуулахад ирлээ.",
    ),
    OrderStatus.SHIPPING: (
        "SHIPPING_STARTED",
        "Хүргэлт эхэллээ",
        "Таны {order_number} дугаартай захиалгын хүргэлт эхэллээ.",
    ),
}


@receiver(post_save, sender=OrderStatusHistory)
def notify_on_order_status_change(sender, instance, created, **kwargs):
    if not created:
        return

    mapping = _ORDER_STATUS_NOTIFICATIONS.get(instance.to_status)
    if mapping is None:
        return

    from apps.notifications.services import NotificationService

    notification_type, title, message_template = mapping
    NotificationService.notify(
        recipient=instance.order.seller,
        notification_type=notification_type,
        title=title,
        message=message_template.format(order_number=instance.order.order_number),
        reference=instance.order.order_number,
    )


@receiver(post_save, sender=Commission)
def notify_on_commission_created(sender, instance, created, **kwargs):
    if not created:
        return

    from apps.notifications.services import NotificationService

    NotificationService.notify(
        recipient=instance.seller,
        notification_type="COMMISSION_CALCULATED",
        title="Шимтгэл бодогдлоо",
        message=(
            f"Таны {instance.order.order_number} дугаартай захиалгад "
            f"{instance.amount}₮ шимтгэл бодогдлоо."
        ),
        reference=instance.order.order_number,
    )
