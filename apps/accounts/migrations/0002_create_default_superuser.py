"""
MERRIGE ERP - Анхдагч админ (superuser) хэрэглэгч үүсгэх data migration.

`migrate` ажиллах үед User хүснэгт үүссэний дараа шууд ажиллаж, нэвтрэх
боломжтой анхны админыг үүсгэнэ. Environment variable шаардлагагүй.
Нууц үгийг hash хэлбэрээр хадгалсан тул код дотор ил харагдахгүй.
Хэрэглэгч аль хэдийн байвал юу ч өөрчлөхгүй.
"""

from django.db import migrations

ADMIN_PHONE_NUMBER = "99112233"
ADMIN_EMAIL = "gantuya8118@gmail.com"
ADMIN_PASSWORD_HASH = (
    "pbkdf2_sha256$1000000$SDqAGhf1cuewJHxFwERMSk$"
    "wrns2uYPj6zNxk41r90YkdS9Q2+olXFg14v72e69lMY="
)


def create_default_superuser(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    if User.objects.filter(phone_number=ADMIN_PHONE_NUMBER).exists():
        return
    User.objects.create(
        phone_number=ADMIN_PHONE_NUMBER,
        email=ADMIN_EMAIL,
        first_name="Admin",
        last_name="Merrige",
        password=ADMIN_PASSWORD_HASH,
        role="ADMIN",
        is_staff=True,
        is_superuser=True,
        is_active=True,
        is_approved=True,
        must_change_password=False,
    )


def remove_default_superuser(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(phone_number=ADMIN_PHONE_NUMBER).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_superuser, remove_default_superuser),
    ]
