from django.core.management.base import BaseCommand

from mediator.models import (
    ActivityRecord,
    AuditLog,
    ConsentRecord,
    GlobalUserProfile,
    HealthMetricRecord,
    Offer,
    SourceUserLink,
)


class Command(BaseCommand):
    help = "Очищает интегрированные данные медиатора, но не удаляет настройки источников."

    def handle(self, *args, **options):
        Offer.objects.all().delete()
        ActivityRecord.objects.all().delete()
        HealthMetricRecord.objects.all().delete()
        ConsentRecord.objects.all().delete()
        SourceUserLink.objects.all().delete()
        GlobalUserProfile.objects.all().delete()
        AuditLog.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Интегрированные данные очищены"))
