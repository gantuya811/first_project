"""
MERRIGE ERP - Ашиг хуваарилалтын анхны (default) утгыг DB-д суулгана.
Эзэн=50%, Үндсэн Борлуулагч=20%, Гэрээт Борлуулагч=30% (спецификейшнд
заасан анхны утга) — код дотор hardcode биш, өгөгдлийн сангийн мигрэйшнээр
нэг удаа суулгаж, дараа нь Админ API-аар өөрчлөх боломжтой.
"""

from decimal import Decimal

from django.db import migrations


def seed_default_distribution(apps, schema_editor):
    ProfitDistributionConfig = apps.get_model("profits", "ProfitDistributionConfig")
    ProfitDistributionConfig.objects.create(
        owner_percentage=Decimal("50.00"),
        main_seller_percentage=Decimal("20.00"),
        contract_seller_percentage=Decimal("30.00"),
        is_active=True,
    )


def remove_default_distribution(apps, schema_editor):
    ProfitDistributionConfig = apps.get_model("profits", "ProfitDistributionConfig")
    ProfitDistributionConfig.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("profits", "0001_initial")]

    operations = [
        migrations.RunPython(seed_default_distribution, remove_default_distribution),
    ]
