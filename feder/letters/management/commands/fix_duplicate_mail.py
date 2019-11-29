from django.core.management.base import BaseCommand
from feder.monitorings.models import Monitoring
from feder.letters.models import Letter
from io import BytesIO
import email
import gzip


class Command(BaseCommand):
    help = "Remove duplicated incoming letters based on 'Message-ID'."

    def add_arguments(self, parser):
        parser.add_argument(
            "--monitoring-pk", help="PK of monitoring which receive mail", required=True
        )
        parser.add_argument(
            "--delete", help="Confirm deletion of email", action="store_true"
        )

    def write_level(self, level, content, *args):
        self.stdout.write("{}{}".format("\t" * level, content.format(*args)))

    def handle(self, *args, **options):
        monitoring = Monitoring.objects.get(pk=options["monitoring_pk"])
        case_count = monitoring.case_set.count()
        removed_count = 0
        for i, case in enumerate(monitoring.case_set.iterator()):
            ids = set()
            self.write_level(
                0, "Processing case: {} (progress: {:.2f}%)", case.pk, i / case_count * 100
            )
            for letter in (
                Letter.objects.filter(record__case=case.pk).is_incoming().all()
            ):
                self.write_level(1, "Processing letter: {}", letter.pk)
                if not letter.eml:
                    self.write_level(2, "Skipping {} due missing eml.", letter.pk)
                    continue
                content = letter.eml.file.read()
                fp = BytesIO(content)
                if b"Subject:" not in content:
                    fp = gzip.GzipFile(fileobj=fp)
                msg = email.message_from_binary_file(fp)
                msg_id = msg.get("Message-ID")
                if not msg_id:
                    self.write_level(
                        2, "Skipping {} due missing 'Message-ID'.", letter.pk
                    )
                    continue
                if msg_id not in ids:
                    self.write_level(
                        2, "Skipping {} due unique 'Message-ID': {}", letter.pk, msg_id
                    )
                    ids.add(msg_id)
                    continue
                self.write_level(
                    2, "Removing {} due duplicated 'Message-ID': {}", letter.pk, msg_id
                )
                removed_count+=1
                if options["delete"]:
                    letter.delete()
        self.write_level(0, "Removed total {} letters", removed_count)
