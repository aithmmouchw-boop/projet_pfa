from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from clinic_common.audit import log_activity
from clinic_common.models import DatabaseBackup, SystemActivity


def create_database_backup(*, created_by=None, notes: str = "") -> DatabaseBackup:
    backup = DatabaseBackup.objects.create(created_by=created_by, notes=notes)
    backup_dir = Path(settings.MEDIA_ROOT) / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = timezone.localtime().strftime("%Y%m%d_%H%M%S")
    filename = f"aesculia_backup_{stamp}_{backup.pk}.json"
    absolute_path = backup_dir / filename

    try:
        with absolute_path.open("w", encoding="utf-8") as handle:
            call_command("dumpdata", indent=2, stdout=handle)
        backup.file_path = str(Path("backups") / filename)
        backup.size_bytes = absolute_path.stat().st_size
        backup.status = DatabaseBackup.Status.SUCCESS
        backup.completed_at = timezone.now()
        backup.save(update_fields=["file_path", "size_bytes", "status", "completed_at"])
        log_activity(
            action=SystemActivity.Action.BACKUP_CREATED,
            description="Sauvegarde de la base de donnees creee",
            actor=created_by,
            metadata={"backup_id": backup.pk, "file_path": backup.file_path},
        )
    except Exception as exc:
        backup.status = DatabaseBackup.Status.FAILED
        backup.error_message = str(exc)
        backup.completed_at = timezone.now()
        backup.save(update_fields=["status", "error_message", "completed_at"])
        raise
    return backup
