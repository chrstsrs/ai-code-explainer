import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Block until the default database is available."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=60,
                            help="Max seconds to wait")

    def handle(self, *args, **opts):
        timeout = int(opts["timeout"])
        self.stdout.write(
            self.style.NOTICE(f"Waiting for database (timeout {timeout}s)..."))
        start = time.time()
        while True:
            try:
                conn = connections["default"]
                conn.cursor()  # touches the DB
            except OperationalError as e:
                if time.time() - start > timeout:
                    raise SystemExit(
                        self.style.ERROR(f"DB not ready after {timeout}s: {e}"))
                time.sleep(1.0)
                continue
            break
        self.stdout.write(self.style.SUCCESS("Database is ready."))
