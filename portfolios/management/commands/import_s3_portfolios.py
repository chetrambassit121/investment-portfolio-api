
import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DatabaseError
from django.utils import timezone

from portfolios.models import Portfolio, ImportLog


logger = logging.getLogger(__name__)

BUCKET_NAME = (
    "investment-portfolio-data-2026-unique-"
    "772325759101-us-east-2-an"
)

OBJECT_KEY = "portfolios.json"


class Command(BaseCommand):
    help = "Import portfolio data from AWS S3 into PostgreSQL"

    def handle(self, *args, **options):

        # Create a record when the import begins.
        import_log = ImportLog.objects.create(
            status="running",
            source="AWS S3",
        )

        created_count = 0
        updated_count = 0

        try:
            s3 = boto3.client(
                "s3",
                region_name="us-east-2",
            )

            response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=OBJECT_KEY,
            )

            raw_data = response["Body"].read()
            data = json.loads(raw_data)

            if isinstance(data, dict):
                data = data.get("portfolios")

            if not isinstance(data, list):
                raise ValueError(
                    "Expected a list of portfolios"
                )

            # Validate and import inside a transaction.
            with transaction.atomic():

                for item in data:

                    if not isinstance(item, dict):
                        raise ValueError(
                            "Invalid portfolio record"
                        )

                    try:
                        name = item["name"]
                        fund_type = item["fund_type"]
                        currency = item["currency"]

                    except KeyError as exc:
                        raise ValueError(
                            f"Missing required field: {exc}"
                        ) from exc

                    portfolio, created = (
                        Portfolio.objects.update_or_create(
                            name=name,
                            defaults={
                                "fund_type": fund_type,
                                "currency": currency,
                            },
                        )
                    )

                    portfolio.full_clean()
                    portfolio.save()

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                    logger.info(
                        "Imported portfolio id=%s name=%s",
                        portfolio.id,
                        portfolio.name,
                    )

            # Only mark success after the transaction commits.
            import_log.status = "success"
            import_log.total_records = len(data)
            import_log.created_count = created_count
            import_log.updated_count = updated_count
            import_log.completed_at = timezone.now()

            import_log.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Import complete: "
                    f"{created_count} created, "
                    f"{updated_count} updated"
                )
            )

        except (
            BotoCoreError,
            ClientError,
            OSError,
            ValueError,
            UnicodeDecodeError,
            KeyError,
            TypeError,
            DatabaseError,
            ValidationError,
        ) as exc:

            logger.exception("S3 portfolio import failed")

            import_log.status = "failed"
            import_log.error_message = str(exc)
            import_log.completed_at = timezone.now()

            import_log.save()

            raise CommandError(
                "Portfolio import failed. Check logs."
            ) from exc
