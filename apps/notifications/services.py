"""
MERRIGE ERP - Мэдэгдлийн Service Layer
Систем дотоод мэдэгдэл (DB-д хадгалагдана) болон Имэйл мэдэгдлийг нэгтгэн
илгээнэ. Имэйл илгээхэд алдаа гарвал (жишээ нь SMTP тохиргоогүй) энэ нь
захиалга/төлбөрийн үндсэн бизнес процессыг ЗОГСООХ ёсгүй тул алдааг
барьж, зөвхөн лог руу бичнэ.

Ирээдүйд SMS сувгийг энд нэмнэ (одоогоор хэрэгжүүлээгүй, спецификейшнд
"Ирээдүйд SMS" гэж тодорхой заасан).
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.notifications.models import Notification

logger = logging.getLogger("django")


class NotificationService:
    @staticmethod
    def notify(recipient, notification_type, title, message, reference=""):
        """Систем дотоод мэдэгдэл үүсгэж, имэйлээр давхар мэдэгдэнэ."""
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            reference=reference,
        )
        NotificationService._send_email(recipient, title, message)
        return notification

    @staticmethod
    def mark_as_read(notification):
        notification.mark_as_read()
        return notification

    @staticmethod
    def mark_all_as_read(user):
        Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )

    @staticmethod
    def _send_email(recipient, title, message):
        if not recipient.email:
            return
        try:
            html_body = render_to_string(
                "emails/notification.html",
                {"user": recipient, "title": title, "message": message},
            )
            send_mail(
                subject=f"MERRIGE ERP - {title}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                html_message=html_body,
                fail_silently=True,
            )
        except Exception:
            logger.exception(
                "Имэйл мэдэгдэл илгээхэд алдаа гарлаа (хүлээн авагч: %s)",
                recipient.email,
            )
