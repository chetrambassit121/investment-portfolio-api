import os
import json
import time
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

import django

# Initialize Django
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from portfolios.models import ImportLog

from django.core.management import call_command

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

AWS_REGION = "us-east-2"

SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION
)


def process_message(message):
    
    """Process an SQS portfolio import job."""

    body = json.loads(message["Body"])

    logger.info("Received SQS message: %s", body)

    job_type = body.get("job_type")
    source = body.get("source")
    file_name = body.get("file")
    import_id = body.get("import_id")

    if job_type != "import_portfolios":
        raise ValueError(
            f"Unsupported job type: {job_type}"
        )

    if source != "s3":
        raise ValueError(
            f"Unsupported source: {source}"
        )

    if file_name != "portfolios.json":
        raise ValueError(
            f"Unsupported file: {file_name}"
        )

    if type(import_id) is not int or import_id <= 0:
        raise ValueError("Missing or invalid import_id")

    with transaction.atomic():
        import_log = (
            ImportLog.objects
            .select_for_update()
            .get(id=import_id)
        )

        if import_log.status == "success":
            logger.info(
                "Import %s already completed. Skipping.",
                import_id,
            )
            return

        if import_log.status == "running":
            raise RuntimeError(
                f"Import {import_id} is already running"
            )

        import_log.status = "running"
        import_log.completed_at = None
        import_log.error_message = ""
        import_log.save(
            update_fields=[
                "status",
                "completed_at",
                "error_message",
            ]
        )

    logger.info(
        "Processing portfolio import: import_id=%s",
        import_id,
    )

    try:
        call_command(
            "import_s3_portfolios",
            import_id=import_id,
        )

    except Exception:
        logger.exception(
            "Portfolio import failed: import_id=%s",
            import_id,
        )
        raise

    logger.info(
        "Import processing finished: import_id=%s",
        import_id,
    )


def start_worker():
    """Continuously poll AWS SQS for messages."""

    logger.info("SQS worker started")

    while True:

        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20,
                VisibilityTimeout=120
            )

            messages = response.get("Messages", [])

            for message in messages:

                try:
                    process_message(message)

                    # Delete only after successful processing
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"]
                    )

                    logger.info(
                        "SQS message processed and deleted"
                    )

                except Exception:
                    logger.exception(
                        "Failed to process SQS message"
                    )

        except (ClientError, BotoCoreError):
            logger.exception("AWS SQS polling error")
            time.sleep(5)

        except Exception:
            logger.exception("Unexpected worker error")
            time.sleep(5)


if __name__ == "__main__":
    start_worker()