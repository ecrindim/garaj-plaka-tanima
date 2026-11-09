"""Son kayıtları listeler. Kullanım: python -m otopark.report"""

from datetime import datetime

from otopark.config import Settings
from otopark.plate_validator import format_for_display
from otopark.visit_repository import VisitRepository


def _format_time(moment: datetime | None) -> str:
    return moment.strftime("%d.%m.%Y %H:%M:%S") if moment else "içeride"


def main() -> None:
    repository = VisitRepository(Settings().database_path)
    try:
        print(f"{'PLAKA':<12} {'GİRİŞ':<20} {'ÇIKIŞ':<20}")
        for visit in repository.recent_visits():
            print(
                f"{format_for_display(visit.plate):<12} "
                f"{_format_time(visit.entry_time):<20} "
                f"{_format_time(visit.exit_time):<20}"
            )
    finally:
        repository.close()


if __name__ == "__main__":
    main()
