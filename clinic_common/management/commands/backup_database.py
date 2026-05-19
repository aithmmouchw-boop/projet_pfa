from django.core.management.base import BaseCommand

from clinic_common.backup import create_database_backup


class Command(BaseCommand):
    help = "Cree une sauvegarde JSON de la base de donnees dans media/backups."

    def add_arguments(self, parser):
        parser.add_argument("--notes", default="", help="Notes associees a la sauvegarde.")

    def handle(self, *args, **options):
        backup = create_database_backup(notes=options["notes"])
        self.stdout.write(
            self.style.SUCCESS(f"Sauvegarde creee: {backup.file_path} ({backup.size_bytes} octets)")
        )
