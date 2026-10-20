import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, DatabaseError
from django.core.exceptions import ValidationError

from portfolios.models import Portfolio

logger = logging.getLogger(__name__)

BUCKET_NAME = (
    "investment-portfolio-data-2026-unique-"
    "772325759101-us-east-2-an"
)

OBJECT_KEY = "portfolios.json"


class Command(BaseCommand):
    help = "Import portfolio data from AWS S3 into PostgreSQL"

    def handle(self, *args, **options):
        s3 = boto3.client("s3", region_name="us-east-2")

        try:
            response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=OBJECT_KEY,
            )

            raw_data = response["Body"].read()
            data = json.loads(raw_data)

        except (BotoCoreError, ClientError, OSError) as exc:
            logger.exception("Failed to read S3 portfolio data")
            raise CommandError("S3 download failed") from exc

        except (ValueError, UnicodeDecodeError) as exc:
            raise CommandError("Invalid JSON in S3 object") from exc

        # Adjust this if your JSON uses a different structure.
        if isinstance(data, dict):
            data = data.get("portfolios")

        if not isinstance(data, list):
            raise CommandError("Expected a list of portfolios")

        created_count = 0
        updated_count = 0

        try:
            with transaction.atomic():

                for item in data:
                    if not isinstance(item, dict):
                        raise CommandError("Invalid portfolio record")

                    try:
                        name = item["name"]
                        fund_type = item["fund_type"]
                        currency = item["currency"]
                    except KeyError as exc:
                        raise CommandError(
                            f"Missing required field: {exc}"
                        ) from exc

                    portfolio, created = Portfolio.objects.update_or_create(
                        name=name,
                        defaults={
                            "fund_type": fund_type,
                            "currency": currency,
                        },
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

        except (DatabaseError, ValidationError) as exc:
            logger.exception("Portfolio import failed")
            raise CommandError("Database import failed") from exc