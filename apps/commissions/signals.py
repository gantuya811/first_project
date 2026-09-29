"""
MERRIGE ERP - Commission Signals
Захиалга COMPLETED төлөвт шилжих бүрд (OrderStatusHistory-ээр дамжуулан)
шимтгэлийг автоматаар тооцоолно. apps.orders нь apps.commissions-ийн
тухай юу ч мэдэхгүй байх ёстой тул хамаарлыг зөв чиглэлд (commissions →
orders) signal-аар холбоно (apps.inventory-ийн STEP6-ийн загвартай адил).

Тэмдэглэл: signal нь OrderService.complete()-ийн ажиллуулж буй ижил
transaction.atomic() дотор синхроноор ажиллана — шимтгэл тооцоолоход
алдаа гарвал (жишээ нь өртгийн мэдээлэл дутуу) захиалгыг COMPLETED
болгох үйлдэл бүхэлдээ буцаагдана (санхүүгийн бүрэн бус захиалга
"дуусах" ёсгүй гэсэн зарчмаар).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.orders.models import OrderStatus, OrderStatusHistory


@receiver(post_save, sender=OrderStatusHistory)
def generate_commission_on_completion(sender, instance, created, **kwargs):
    if not created or instance.to_status != OrderStatus.COMPLETED:
        return

    from apps.commissions.services import CommissionService

    CommissionService.generate_for_order(instance.order, actor=instance.created_by)
