from django.core.management.base import BaseCommand

from mediator.models import DataSource
from mediator.services import sync_all_sources, sync_source


class Command(BaseCommand):
    help = "Синхронизирует данные из локальных клиентов в глобальную схему медиатора."

    def add_arguments(self, parser):
        parser.add_argument("--source", dest="source_id", help="Синхронизировать только один источник по source_id")

    def handle(self, *args, **options):
        source_id = options.get("source_id")
        if source_id:
            source = DataSource.objects.get(source_id=source_id)
            results = [sync_source(source).as_dict()]
        else:
            results = sync_all_sources(active_only=True)

        for result in results:
            if result["errors"]:
                self.stdout.write(self.style.ERROR(f"{result['source_id']}: ошибка — {result['errors']}"))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{result['source_id']}: загружено {result['loaded']}, "
                        f"создано профилей {result['created_profiles']}, "
                        f"обновлено {result['updated_profiles']}, "
                        f"активностей {result['activities']}, показателей {result['metrics']}"
                    )
                )
